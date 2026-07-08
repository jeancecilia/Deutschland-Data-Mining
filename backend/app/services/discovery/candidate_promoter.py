"""
Candidate Promoter — promotes validated niche_candidates to the keywords table
so the existing KDP pipeline can process them.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import NicheCandidate, NicheCandidateKeyword
from app.models.keyword import Keyword
from app.services.keyword_intelligence import infer_keyword_intelligence


@dataclass
class PromoteBatch:
    promoted: int
    skipped: int
    keywords: list[Keyword]


def promote_candidates_to_seeds(
    db: Session,
    *,
    limit: int = 50,
    min_score: int = 50,
) -> PromoteBatch:
    """Promote fast-validated niche candidates to seed keywords.

    Only promotes candidates with status='fast_validated' and
    fast_validation_score >= min_score.
    """
    candidates = list(
        db.scalars(
            select(NicheCandidate)
            .where(
                NicheCandidate.status == "fast_validated",
                NicheCandidate.fast_validation_score >= min_score,
            )
            .order_by(NicheCandidate.fast_validation_score.desc())
            .limit(limit)
        )
    )

    promoted = 0
    skipped = 0
    result_keywords: list[Keyword] = []

    for candidate in candidates:
        # Check if already promoted as keyword (by candidate name)
        existing_keyword = db.scalars(
            select(Keyword).where(
                Keyword.source_niche_candidate_id == candidate.id,
            )
        ).first()
        if existing_keyword is not None:
            skipped += 1
            continue

        # Also check by phrase match
        phrase_matches = db.scalars(
            select(Keyword).where(Keyword.keyword == candidate.candidate_name)
        ).first()
        if phrase_matches is not None:
            # Link existing keyword back to candidate
            phrase_matches.source_niche_candidate_id = candidate.id
            phrase_matches.discovery_origin_type = "initial_discovery"
            db.add(phrase_matches)
            candidate.status = "promoted_to_seed"
            db.add(candidate)
            result_keywords.append(phrase_matches)
            promoted += 1
            continue

        # Infer intelligence for the new keyword
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
            risk_level=candidate.risk_level or intelligence.risk_level,
            status="discovered",
            priority=candidate.fast_validation_score or 60,
            notes=f"Auto-promoted from discovery candidate #{candidate.id}: {candidate.candidate_name}",
        )
        db.add(keyword)
        db.flush()

        # Also generate keyword variants for the candidate
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
        candidate.promotion_reason = f"Auto-promoted with score {candidate.fast_validation_score}"
        db.add(candidate)
        result_keywords.append(keyword)
        promoted += 1

    db.commit()
    for kw in result_keywords:
        db.refresh(kw)

    return PromoteBatch(
        promoted=promoted,
        skipped=skipped,
        keywords=result_keywords,
    )


def _generate_keyword_variants(phrase: str) -> list[dict]:
    """Generate keyword variants from a niche candidate phrase."""
    variants: list[dict] = []
    lowered = phrase.casefold()

    # Primary (exact)
    variants.append({"text": phrase, "type": "primary", "confidence": 90})

    # Lowercase variant
    if phrase != lowered:
        variants.append({"text": lowered, "type": "variant", "confidence": 85})

    # Remove 'für' construction → compound
    if " für " in lowered:
        parts = lowered.split(" für ", 1)
        compound = parts[0].strip() + " " + parts[1].strip()
        variants.append({"text": compound, "type": "variant", "confidence": 70})

        # Reversed: "audience topic"
        reversed_phrase = parts[1].strip() + " " + parts[0].strip()
        variants.append({"text": reversed_phrase, "type": "variant", "confidence": 65})

    # Add "Buch" suffix
    variants.append({"text": lowered + " buch", "type": "long_tail", "confidence": 60})

    # Add "Ratgeber" suffix
    variants.append({"text": lowered + " ratgeber", "type": "long_tail", "confidence": 55})

    return variants[:8]  # Limit to 8 variants
