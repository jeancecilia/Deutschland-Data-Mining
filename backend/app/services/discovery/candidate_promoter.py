"""
Candidate Promoter v2 — manual review gate, respects DISCOVERY_AUTO_PROMOTE_ENABLED.

Risk rules:
  - blocked/restricted: NEVER promotable
  - high: only promotable after manual approval (status=approved_for_promotion)
  - low/medium: promotable when approved or auto-promote enabled
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.discovery_pipeline import NicheCandidate, NicheCandidateKeyword
from app.models.keyword import Keyword
from app.services.keyword_intelligence import infer_keyword_intelligence


@dataclass
class PromoteBatch:
    promoted: int
    skipped: int
    skipped_auto_blocked: int
    skipped_risk: int
    keywords: list[Keyword]


def promote_candidates_to_seeds(
    db: Session,
    *,
    limit: int = 50,
    min_score: int = 50,
    force: bool = False,
) -> PromoteBatch:
    """Promote candidates to seed keywords.

    Rules:
      - blocked/restricted: never promoted
      - high risk: only after manual approval (status=approved_for_promotion)
      - low/medium: when approved, or if auto-promote is enabled + auto_promote_allowed
    """
    settings = get_settings()
    auto_promote_enabled = settings.discovery_auto_promote_enabled

    if auto_promote_enabled or force:
        # Auto-promote eligible candidates + approved ones
        candidates = list(
            db.scalars(
                select(NicheCandidate)
                .where(
                    (
                        (NicheCandidate.status == "approved_for_promotion")
                        | (
                            (NicheCandidate.status == "fast_validated")
                            & (NicheCandidate.auto_promote_allowed == True)  # noqa: E712
                        )
                    ),
                    NicheCandidate.risk_category.notin_(["blocked", "restricted"]),
                    NicheCandidate.fast_validation_score >= min_score,
                )
                .order_by(NicheCandidate.fast_validation_score.desc().nullslast())
                .limit(limit)
            )
        )
    else:
        # Manual approval gate only
        candidates = list(
            db.scalars(
                select(NicheCandidate)
                .where(NicheCandidate.status == "approved_for_promotion")
                .order_by(NicheCandidate.fast_validation_score.desc().nullslast())
                .limit(limit)
            )
        )

    promoted = 0
    skipped = 0
    skipped_auto_blocked = 0
    skipped_risk = 0
    result_keywords: list[Keyword] = []

    for candidate in candidates:
        # NEVER promote blocked/restricted
        if candidate.risk_category in ("blocked", "restricted"):
            skipped_risk += 1
            continue

        # High risk: only if manually approved (status already checked by query)
        if candidate.risk_category == "high" and candidate.status != "approved_for_promotion":
            skipped_risk += 1
            continue

        # Check if already promoted
        existing_keyword = db.scalars(
            select(Keyword).where(
                Keyword.source_niche_candidate_id == candidate.id,
            )
        ).first()
        if existing_keyword is not None:
            candidate.status = "promoted_to_seed"
            candidate.promotion_reason = "Already promoted (existing keyword)"
            db.add(candidate)
            skipped += 1
            continue

        # Check phrase match
        phrase_matches = db.scalars(
            select(Keyword).where(Keyword.keyword == candidate.candidate_name)
        ).first()
        if phrase_matches is not None:
            phrase_matches.source_niche_candidate_id = candidate.id
            phrase_matches.discovery_origin_type = "initial_discovery"
            db.add(phrase_matches)
            candidate.status = "promoted_to_seed"
            db.add(candidate)
            result_keywords.append(phrase_matches)
            promoted += 1
            continue

        intelligence = infer_keyword_intelligence(
            candidate.candidate_name,
            book_type=candidate.book_class_guess,
        )

        keyword = Keyword(
            keyword=candidate.candidate_name,
            language=candidate.language,
            marketplace=candidate.marketplace,
            keyword_type="discovery_seed",
            source_niche_candidate_id=candidate.id,
            discovery_origin_type="initial_discovery",
            target_audience=intelligence.target_audience,
            category_hint=intelligence.category_hint,
            search_intent_family=intelligence.search_intent_family,
            specificity_score=intelligence.specificity_score,
            intent_score=intelligence.intent_score,
            audience_clarity_score=intelligence.audience_clarity_score,
            format_suitability_score=intelligence.format_suitability_score,
            competition_probability_score=intelligence.competition_probability_score,
            production_effort_score=intelligence.production_effort_score,
            book_type=candidate.book_class_guess,
            risk_level=candidate.risk_category or intelligence.risk_level,
            status="discovered",
            priority=candidate.fast_validation_score or 60,
            notes=f"Discovery seed from candidate #{candidate.id}: {candidate.candidate_name}",
        )
        db.add(keyword)
        db.flush()

        # Generate keyword variants
        variants = _generate_keyword_variants(candidate.candidate_name)
        for variant in variants:
            db.add(NicheCandidateKeyword(
                niche_candidate_id=candidate.id,
                keyword=variant["text"],
                keyword_type=variant["type"],
                language=candidate.language,
                confidence=variant.get("confidence", 50),
            ))

        candidate.status = "promoted_to_seed"
        candidate.promotion_reason = "Approved and promoted"
        db.add(candidate)
        result_keywords.append(keyword)
        promoted += 1

    db.commit()
    for kw in result_keywords:
        db.refresh(kw)

    return PromoteBatch(
        promoted=promoted,
        skipped=skipped,
        skipped_auto_blocked=skipped_auto_blocked,
        skipped_risk=skipped_risk,
        keywords=result_keywords,
    )


def _generate_keyword_variants(phrase: str) -> list[dict]:
    variants: list[dict] = []
    lowered = phrase.casefold()
    variants.append({"text": phrase, "type": "primary", "confidence": 90})
    if phrase != lowered:
        variants.append({"text": lowered, "type": "variant", "confidence": 85})
    if " für " in lowered:
        parts = lowered.split(" für ", 1)
        variants.append({"text": parts[0].strip() + " " + parts[1].strip(), "type": "variant", "confidence": 70})
    variants.append({"text": lowered + " buch", "type": "long_tail", "confidence": 60})
    variants.append({"text": lowered + " ratgeber", "type": "long_tail", "confidence": 55})
    return variants[:8]
