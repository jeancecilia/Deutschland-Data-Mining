"""
Candidate Ranker — scores candidates for validation priority.

Delegates semantic scoring to candidate_quality_gate.py and applies
relative duplication penalties and domain quotas before queuing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import text, select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import DiscoveryEntity, NicheCandidate
from app.services.discovery.entity_normalizer import normalize_entity_name
from app.services.discovery.candidate_quality_gate import evaluate_candidate_quality

@dataclass
class RankResult:
    ranked: int
    queued: int
    manual_review: int
    rejected_pre_validation: int
    top_score: int
    avg_score: float

def _score_duplication(
    candidate_name: str, normalized: str,
    macro_domain: str | None,
    domain_candidates: dict[str, list[tuple[str, int]]],
    candidate_id: int | None = None,
) -> int:
    if not macro_domain:
        return 0
    siblings = domain_candidates.get(macro_domain, [])
    if not siblings:
        return 0
    name_words = set(candidate_name.lower().split())
    similar = 0
    for sib_name, sib_id in siblings:
        if candidate_id is not None and sib_id == candidate_id:
            continue
        sib_words = set(sib_name.lower().split())
        overlap = len(name_words & sib_words) / max(len(name_words), 1)
        if overlap > 0.7:
            similar += 1
    if similar >= 3: return 80
    if similar >= 2: return 50
    if similar >= 1: return 20
    return 0

def rank_candidates_for_validation(
    db: Session,
    *,
    limit: int = 5000,
    min_score: int = 70,
    max_per_macro_domain: int = 100,
    max_per_subdomain: int = 30,
    max_per_micro_domain: int = 3,
) -> RankResult:
    """Two-phase ranking: score all candidates first, then sort by score,
    then apply domain quotas in score-descending order.

    Thresholds:
        queued_threshold  = min_score
        manual_threshold  = max(0, min_score - 10)
    """
    candidates = list(db.scalars(
        select(NicheCandidate).where(
            NicheCandidate.status == "new"
        ).order_by(NicheCandidate.id.asc()).limit(limit)
    ))

    if not candidates:
        return RankResult(0, 0, 0, 0, 0, 0.0)

    # Load entity names for resolution
    entity_map: dict[int, str] = {}
    for e in db.scalars(select(DiscoveryEntity)):
        entity_map[e.id] = e.name

    domain_index: dict[str, list[tuple[str, int]]] = {}
    for c in candidates:
        se = c.source_entities or {}
        macro = se.get("macro_domain", se.get("domain", ""))
        if macro:
            domain_index.setdefault(str(macro), []).append((c.candidate_name, c.id))

    queue_threshold = min_score
    manual_threshold = max(0, min_score - 10)

    # ── Phase 1: score every candidate without assigning status ──
    scored: list[tuple[int, NicheCandidate, dict, int]] = []
    all_scores: list[int] = []

    for candidate in candidates:
        se = candidate.source_entities or {}
        macro = str(se.get("macro_domain", se.get("domain", "")))
        sub = str(se.get("subdomain", ""))
        micro = str(se.get("micro_domain", ""))
        name = candidate.candidate_name

        topic_name = entity_map.get(candidate.main_topic_entity_id) if candidate.main_topic_entity_id else None
        audience_name = entity_map.get(candidate.audience_entity_id) if candidate.audience_entity_id else None
        problem_name = entity_map.get(candidate.problem_entity_id) if candidate.problem_entity_id else None
        format_name = entity_map.get(candidate.format_entity_id) if candidate.format_entity_id else None

        gate_result = evaluate_candidate_quality(
            candidate_name=name,
            topic_name=topic_name,
            audience_name=audience_name,
            problem_name=problem_name,
            format_name=format_name,
            meta=se,
        )

        dup = _score_duplication(name, candidate.normalized_name, macro, domain_index, candidate.id)

        pre_val = gate_result.total_score - dup
        pre_val = max(0, min(100, pre_val))

        # ── Queued Gating: prevent old broad/template candidates from entering queue ──
        canonical = str(se.get("canonical_micro_domain") or "")
        is_canonical = False
        if canonical:
            is_canonical = normalize_entity_name(name) == normalize_entity_name(canonical)

        lower_name = name.lower()
        queue_eligible = se.get("queue_eligible", True)

        is_auto_generated_variant = se.get("variant_type") == "generated_variant"
        is_suffix_variant = (
            is_auto_generated_variant
            and ("hilfe bei" in lower_name or "schritt-für-schritt" in lower_name)
        )

        has_duplicate_format = any([
            "checkliste checkliste" in lower_name,
            "tagebuch tagebuch" in lower_name,
            "arbeitsbuch arbeitsbuch" in lower_name,
            "planer planer" in lower_name,
            "ratgeber ratgeber" in lower_name,
        ])

        has_double_fuer = "für für" in lower_name
        has_no_metadata = not canonical and not macro and not micro
        too_long = len(name.split()) > 8

        # Hard rejection
        if not gate_result.allowed:
            pre_val = min(pre_val, 59)
        if (
            is_suffix_variant
            or has_duplicate_format
            or has_double_fuer
            or has_no_metadata
        ):
            pre_val = min(pre_val, 59)
        elif canonical and not is_canonical:
            pre_val = min(pre_val, 69)
        elif queue_eligible is False:
            pre_val = min(pre_val, 69)
        elif too_long:
            pre_val = min(pre_val, 69)

        if isinstance(dup, (int, float)) and dup >= 80 and not is_canonical:
            pre_val = min(pre_val, 59)
        if isinstance(dup, (int, float)) and dup >= 50 and not is_canonical:
            pre_val = min(pre_val, 69)

        all_scores.append(pre_val)
        scored.append((pre_val, candidate, se, dup))

    # ── Phase 2: sort by score desc, then apply quotas ──
    scored.sort(key=lambda x: (-x[0], x[1].id))

    macro_counts: dict[str, int] = {}
    sub_counts: dict[str, int] = {}
    micro_counts: dict[str, int] = {}

    # Preload existing queued counts
    queued_candidates = list(db.scalars(
        select(NicheCandidate.source_entities).where(
            NicheCandidate.status == "prevalidation_queued"
        )
    ))
    for se_dict in queued_candidates:
        se_dict = se_dict or {}
        macro = str(se_dict.get("macro_domain", se_dict.get("domain", "")))
        sub = str(se_dict.get("subdomain", ""))
        micro = str(se_dict.get("micro_domain", ""))
        if macro:
            macro_counts[macro] = macro_counts.get(macro, 0) + 1
        if sub:
            sub_counts[sub] = sub_counts.get(sub, 0) + 1
        if micro:
            micro_counts[micro] = micro_counts.get(micro, 0) + 1
            
    queued = 0
    manual_review = 0
    rejected = 0
    top_score = 0

    for pre_val, candidate, se, dup in scored:
        macro = str(se.get("macro_domain", se.get("domain", "")))
        sub = str(se.get("subdomain", ""))
        micro = str(se.get("micro_domain", ""))
        top_score = max(top_score, pre_val)

        status = "rejected_pre_validation"
        if pre_val >= queue_threshold:
            if max_per_macro_domain and macro and macro_counts.get(macro, 0) >= max_per_macro_domain:
                status = "manual_review"
            elif max_per_subdomain and sub and sub_counts.get(sub, 0) >= max_per_subdomain:
                status = "manual_review"
            elif max_per_micro_domain and micro and micro_counts.get(micro, 0) >= max_per_micro_domain:
                status = "manual_review"
            else:
                status = "queued"
                macro_counts[macro] = macro_counts.get(macro, 0) + 1
                sub_counts[sub] = sub_counts.get(sub, 0) + 1
                micro_counts[micro] = micro_counts.get(micro, 0) + 1
        elif pre_val >= manual_threshold:
            status = "manual_review"
        else:
            status = "rejected_pre_validation"

        if status == "queued":
            queued += 1
        elif status == "manual_review":
            manual_review += 1
        else:
            rejected += 1

        new_se = dict(se)
        new_se["pre_validation_score"] = pre_val
        new_se["duplication_score"] = dup
        new_se["validation_queue_status"] = status
        new_se["validation_priority"] = pre_val
        
        # Remove old nested scores
        for k in ["naturalness_score", "specificity_score", "intent_score", "domain_fit_score", "format_fit_score", "audience_fit_score", "format_style_score"]:
            new_se.pop(k, None)
            
        candidate.source_entities = new_se

        # ── Update lifecycle status to match pre-validation result ──
        status_map = {
            "queued": "prevalidation_queued",
            "manual_review": "prevalidation_manual_review",
            "rejected_pre_validation": "rejected_pre_validation",
        }
        candidate.status = status_map.get(status, candidate.status)

    db.commit()
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

    return RankResult(
        ranked=len(candidates),
        queued=queued,
        manual_review=manual_review,
        rejected_pre_validation=rejected,
        top_score=top_score,
        avg_score=round(avg_score, 1),
    )
