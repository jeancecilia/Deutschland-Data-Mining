"""
Candidate Ranker — scores candidates for validation priority.

Uses source_entities JSONB to store ranking scores (no migration needed).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from collections import Counter

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.discovery.format_fit_rules import score_format_fit

HIGH_INTENT_WORDS = {
    "tagebuch", "arbeitsbuch", "workbook", "planer", "checkliste",
    "ratgeber", "leitfaden", "journal", "tracker", "vorlagen",
    "trainingsjournal", "logbuch", "praxisbuch", "notizbuch",
}

GENERIC_FILLER = {
    "dinge", "sachen", "zeug", "kram", "thema", "bereich",
}


@dataclass
class RankResult:
    ranked: int
    queued: int
    manual_review: int
    rejected_pre_validation: int
    top_score: int
    avg_score: float


def _score_naturalness(candidate_name: str) -> int:
    """Score how natural the phrase sounds. 0=awkward, 100=natural."""
    score = 100
    lowered = candidate_name.lower()
    words = lowered.split()

    # Repeated format words
    word_counts = Counter(words)
    for w, c in word_counts.items():
        if c > 2 and w not in {"für", "und", "mit", "der", "die", "das", "den", "dem"}:
            score -= 15
            break

    # Too many "für"
    fuer_count = lowered.count(" für ")
    if fuer_count > 2:
        score -= 20
    elif fuer_count > 1:
        score -= 10

    # Phrase too long
    if len(words) > 12:
        score -= 15
    elif len(words) > 8:
        score -= 5

    # Same word repeated
    for w, c in word_counts.items():
        if c > 2 and len(w) > 3:
            score -= 10
            break

    # Generic filler
    for filler in GENERIC_FILLER:
        if filler in words:
            score -= 10
            break

    return max(0, score)


def _score_specificity(candidate_name: str, meta: dict | None) -> int:
    """Score 0–100 based on topic/audience/problem/format presence."""
    score = 0
    if meta:
        if meta.get("macro_domain") or meta.get("micro_domain"):
            score += 25  # topic
        if meta.get("audience_hint"):
            score += 25  # audience
        if meta.get("problem_hint"):
            score += 25  # problem
        if meta.get("format_hint"):
            score += 25  # format

    # Also check from text
    lowered = candidate_name.lower()
    if " für " in lowered:
        score = max(score, 50)  # at least audience/topic pair
    if any(w in lowered for w in ["checkliste", "tagebuch", "arbeitsbuch", "planer", "ratgeber"]):
        score = max(score, score + 10)
    return min(100, score)


def _score_intent(candidate_name: str, meta: dict | None) -> int:
    """Score 0–100 based on KDP buyer intent signals."""
    score = 0
    lowered = candidate_name.lower()
    for word in HIGH_INTENT_WORDS:
        if word in lowered:
            score += 15
    score = min(45, score)

    if " für " in lowered:
        score += 10  # audience
    if meta and meta.get("problem_hint"):
        score += 10  # clear use case
    return min(100, score)


def _score_domain_fit(meta: dict | None) -> int:
    """Score 0–100 based on domain metadata presence."""
    if not meta:
        return 10
    score = 0
    # Accept "domain" as fallback for "macro_domain"
    if meta.get("macro_domain") or meta.get("domain"):
        score += 30
    if meta.get("subdomain"):
        score += 30
    if meta.get("micro_domain"):
        score += 40
    return score


def _score_duplication(
    candidate_name: str,
    normalized: str,
    macro_domain: str | None,
    domain_candidates: dict[str, list[tuple[str, int]]],
) -> int:
    """Score 0–100 for duplication (higher = more duplicated)."""
    if not macro_domain:
        return 0

    siblings = domain_candidates.get(macro_domain, [])
    if not siblings:
        return 0

    # Check if same topic+audience with different format
    name_words = set(candidate_name.lower().split())
    similar = 0
    for sib_name, _ in siblings:
        sib_words = set(sib_name.lower().split())
        overlap = len(name_words & sib_words) / max(len(name_words), 1)
        if overlap > 0.7:
            similar += 1

    if similar >= 3:
        return 80
    if similar >= 2:
        return 50
    if similar >= 1:
        return 20
    return 0


def rank_candidates_for_validation(
    db: Session,
    *,
    limit: int = 5000,
    min_score: int = 60,
    max_per_macro_domain: int = 100,
    max_per_subdomain: int = 30,
    max_per_micro_domain: int = 3,
) -> RankResult:
    """Rank all new candidates and assign queue status."""
    from sqlalchemy import select as sa_select
    from app.models.discovery_pipeline import NicheCandidate

    # Get all new candidates
    candidates = list(db.scalars(
        sa_select(NicheCandidate).where(
            NicheCandidate.status.in_(["new", "needs_manual_review"])
        ).limit(limit)
    ))

    if not candidates:
        return RankResult(0, 0, 0, 0, 0, 0.0)

    # Build domain candidate index for duplication check
    domain_index: dict[str, list[tuple[str, int]]] = {}
    for c in candidates:
        se = c.source_entities or {}
        macro = se.get("macro_domain", se.get("domain", ""))
        if macro:
            domain_index.setdefault(str(macro), []).append((c.candidate_name, c.id))

    # Counters for diversity caps
    macro_counts: dict[str, int] = {}
    sub_counts: dict[str, int] = {}
    micro_counts: dict[str, int] = {}

    queued = 0
    manual_review = 0
    rejected = 0
    all_scores = []
    top_score = 0

    for candidate in candidates:
        se = candidate.source_entities or {}
        macro = str(se.get("macro_domain", se.get("domain", "")))
        sub = str(se.get("subdomain", ""))
        micro = str(se.get("micro_domain", ""))

        name = candidate.candidate_name
        norm = candidate.normalized_name

        # Score components
        nat = _score_naturalness(name)
        spec = _score_specificity(name, se)
        intent = _score_intent(name, se)
        dom_fit = _score_domain_fit(se)
        fmt_fit = score_format_fit(name, macro, sub)
        dup = _score_duplication(name, norm, macro, domain_index)

        pre_val = int(
            nat * 0.25 + spec * 0.20 + intent * 0.20 +
            dom_fit * 0.15 + fmt_fit * 0.15 - dup * 0.15
        )
        pre_val = max(0, min(100, pre_val))
        all_scores.append(pre_val)
        top_score = max(top_score, pre_val)

        # Determine queue status with diversity caps
        status = "rejected_pre_validation"
        if pre_val >= 75:
            # Check caps
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
        elif pre_val >= 60:
            status = "manual_review"
        elif pre_val < 60:
            status = "rejected_pre_validation"

        if status == "queued":
            queued += 1
        elif status == "manual_review":
            manual_review += 1
        else:
            rejected += 1

        # Store scores in source_entities
        new_se = dict(se)
        new_se["pre_validation_score"] = pre_val
        new_se["naturalness_score"] = nat
        new_se["specificity_score"] = spec
        new_se["intent_score"] = intent
        new_se["domain_fit_score"] = dom_fit
        new_se["format_fit_score"] = fmt_fit
        new_se["duplication_score"] = dup
        new_se["validation_queue_status"] = status
        new_se["validation_priority"] = pre_val
        candidate.source_entities = new_se

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
