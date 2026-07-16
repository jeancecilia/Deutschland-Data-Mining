"""
Fast Validator v2 — quality-hardened pre-validation with semantic compatibility.

Key changes:
  - Semantic compatibility check between topic and audience
  - Risk classification (low/medium/high/restricted/blocked)
  - Penalties for semantic mismatches
  - Rewards for domain-verified pairs
  - Auto-promotion disabled by default
  - Recommendation labels: GO, MAYBE, NO-GO, REVIEW_REQUIRED, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import DiscoveryEntity, NicheCandidate
from app.services.discovery.domain_compatibility_rules import classify_risk
from app.services.discovery.semantic_compatibility import (
    check_semantic_compatibility,
    get_rewrite_suggestions,
)

RECOMMEND_GO = "GO"
RECOMMEND_MAYBE = "MAYBE"
RECOMMEND_NO_GO = "NO-GO"
RECOMMEND_REVIEW = "REVIEW_REQUIRED"
RECOMMEND_HIGH_RISK = "HIGH_RISK_OPPORTUNITY"
RECOMMEND_BLOCKED = "BLOCKED"

# Words that indicate a strong format match
STRONG_FORMAT_WORDS = {
    "tagebuch", "planer", "workbook", "checkliste", "ratgeber",
    "leitfaden", "arbeitsbuch", "logbuch", "tracker", "journal",
    "lernplaner", "übungsbuch", "praxisbuch", "handbuch",
    "trainingsbuch", "kochbuch",
}

EVERGREEN_SIGNALS = {
    "prüfung", "examen", "abitur", "führerschein", "ausbildung",
    "pflege", "erziehung", "ernährung", "haushalt", "wohnung",
    "gesundheit", "rente", "altersvorsorge", "bewerbung",
    "selbstständigkeit", "existenzgründung", "steuer",
}


@dataclass(frozen=True)
class FastValidationResult:
    candidate_id: int
    score: int
    compatibility_score: int
    specificity_score: int
    audience_clarity_score: int
    format_fit_score: int
    book_potential_score: int
    evergreen_score: int
    risk_penalty: int
    risk_category: str
    risk_reason_codes: list[str] = field(default_factory=list)
    manual_review_required: bool = False
    auto_promote_allowed: bool = False
    recommendation_label: str = RECOMMEND_REVIEW
    reason: str = ""
    suggested_rewrites: list[str] = field(default_factory=list)


def validate_candidates_fast(
    db: Session,
    *,
    limit: int = 100,
) -> list[FastValidationResult]:
    """Fast-validate new niche candidates with quality hardening."""
    candidates = list(
        db.scalars(
            select(NicheCandidate)
            .where(NicheCandidate.status.in_(["prevalidation_queued", "needs_manual_review"]))
            .order_by(NicheCandidate.confidence.desc())
            .limit(limit)
        )
    )

    # Load entity names for resolution
    entity_map: dict[int, str] = {}
    entity_type_map: dict[int, str] = {}
    for e in db.scalars(select(DiscoveryEntity)):
        entity_map[e.id] = e.name
        entity_type_map[e.id] = e.entity_type

    results: list[FastValidationResult] = []
    for candidate in candidates:
        # Resolve entity names
        topic_name = entity_map.get(candidate.main_topic_entity_id) if candidate.main_topic_entity_id else None
        audience_name = entity_map.get(candidate.audience_entity_id) if candidate.audience_entity_id else None
        problem_name = entity_map.get(candidate.problem_entity_id) if candidate.problem_entity_id else None

        result = _validate_one(candidate, topic_name, audience_name)

        # Update candidate
        candidate.fast_validation_score = result.score
        candidate.compatibility_score = result.compatibility_score
        candidate.risk_category = result.risk_category
        candidate.risk_reason_codes = result.risk_reason_codes
        candidate.manual_review_required = result.manual_review_required
        candidate.auto_promote_allowed = result.auto_promote_allowed
        candidate.recommendation_label = result.recommendation_label
        candidate.authority_required = "expert_review_required" in result.risk_reason_codes
        candidate.disclaimer_required = result.risk_category in ("high", "restricted")
        candidate.suggested_rewrites = result.suggested_rewrites if result.suggested_rewrites else None

        # Set status
        if result.recommendation_label == RECOMMEND_BLOCKED:
            candidate.status = "blocked"
            candidate.rejection_reason = result.reason
        elif result.recommendation_label == RECOMMEND_NO_GO:
            candidate.status = "rejected"
            candidate.rejection_reason = result.reason
        elif result.recommendation_label in (RECOMMEND_REVIEW, RECOMMEND_HIGH_RISK):
            candidate.status = "needs_manual_review"
            candidate.promotion_reason = result.reason
        elif result.auto_promote_allowed and result.recommendation_label == RECOMMEND_GO:
            candidate.status = "fast_validated"
            candidate.promotion_reason = result.reason
        else:
            candidate.status = "needs_manual_review"
            candidate.promotion_reason = result.reason

        db.add(candidate)
        results.append(result)

    db.commit()
    return results


def _validate_one(
    candidate: NicheCandidate,
    topic_name: str | None,
    audience_name: str | None,
) -> FastValidationResult:
    phrase = candidate.candidate_name.casefold()

    # ── Step 1: Semantic compatibility (MOST IMPORTANT) ──────────
    compat = check_semantic_compatibility(topic_name, audience_name)
    compat_score = compat.score

    # Hard block for incompatible pairs
    if compat.hard_block:
        return FastValidationResult(
            candidate_id=candidate.id,
            score=max(0, compat_score - 30),
            compatibility_score=compat_score,
            specificity_score=30,
            audience_clarity_score=20,
            format_fit_score=20,
            book_potential_score=10,
            evergreen_score=10,
            risk_penalty=40,
            risk_category="low",
            recommendation_label=RECOMMEND_NO_GO,
            auto_promote_allowed=False,
            manual_review_required=False,
            reason=f"Semantic mismatch: {compat.reason}",
            suggested_rewrites=get_rewrite_suggestions(topic_name, audience_name),
        )

    # ── Step 2: Risk classification ─────────────────────────────
    risk_category, risk_codes, manual_review = classify_risk(phrase, topic_name)

    risk_penalty = 0
    if risk_category == "blocked":
        return FastValidationResult(
            candidate_id=candidate.id,
            score=0,
            compatibility_score=compat_score,
            specificity_score=0,
            audience_clarity_score=0,
            format_fit_score=0,
            book_potential_score=0,
            evergreen_score=0,
            risk_penalty=100,
            risk_category="blocked",
            risk_reason_codes=risk_codes,
            recommendation_label=RECOMMEND_BLOCKED,
            auto_promote_allowed=False,
            manual_review_required=True,
            reason="Blocked: contains prohibited content indicators",
        )
    elif risk_category == "restricted":
        risk_penalty = 50
    elif risk_category == "high":
        risk_penalty = 30
    elif risk_category == "medium":
        risk_penalty = 10

    # ── Step 3: Specificity ──────────────────────────────────────
    word_count = len(phrase.split())
    specificity = min(100, max(20, word_count * 15))
    if "für" in phrase:
        specificity += 5

    # ── Step 4: Audience clarity ─────────────────────────────────
    audience_score = 20
    if audience_name:
        audience_score = min(100, audience_score + 35)
    if "für" in phrase:
        audience_score = min(100, audience_score + 15)

    # ── Step 5: Format fit ───────────────────────────────────────
    format_score = 25
    if any(w in phrase for w in STRONG_FORMAT_WORDS):
        format_score = min(100, format_score + 35)
    if candidate.format_entity_id:
        format_score = min(100, format_score + 25)

    # ── Step 6: Book potential ───────────────────────────────────
    book_score = 20
    if candidate.book_class_guess == "sachbuch":
        book_score += 25
    elif candidate.book_class_guess == "medium_content":
        book_score += 15
    if compat_score >= 70:
        book_score += 15
    if audience_score >= 50:
        book_score += 5

    # ── Step 7: Evergreen ────────────────────────────────────────
    evergreen_score = 15
    if any(w in phrase for w in EVERGREEN_SIGNALS):
        evergreen_score = min(100, evergreen_score + 30)
    if risk_category == "low":
        evergreen_score += 10

    # ── Penalties ────────────────────────────────────────────────
    if compat_score < 40:
        specificity = max(0, specificity - 30)
    if compat_score < 60:
        book_score = max(0, book_score - 20)
    if risk_category == "high" and not manual_review:
        risk_penalty += 20
    if risk_category == "restricted":
        book_score = max(0, book_score - 30)

    # ── Boost for good compatibility ─────────────────────────────
    if compat_score >= 90:
        book_score = min(100, book_score + 15)
    if compat_score >= 75:
        specificity = min(100, specificity + 10)

    # ── Final score ──────────────────────────────────────────────
    score = max(0, min(100, (
        specificity * 0.20
        + audience_score * 0.15
        + format_score * 0.12
        + book_score * 0.25
        + evergreen_score * 0.10
        + compat_score * 0.18
        - risk_penalty * 0.15
    )))

    # ── Recommendation ───────────────────────────────────────────
    recommendation = RECOMMEND_REVIEW
    auto_promote = False

    if risk_category in ("restricted", "blocked"):
        recommendation = RECOMMEND_BLOCKED
        auto_promote = False
    elif risk_category == "high":
        recommendation = RECOMMEND_HIGH_RISK
        auto_promote = False
    elif score >= 75 and compat_score >= 70:
        recommendation = RECOMMEND_GO
        auto_promote = True  # Will be gated by DISCOVERY_AUTO_PROMOTE_ENABLED
    elif score >= 55:
        recommendation = RECOMMEND_MAYBE
        auto_promote = False
    elif score >= 30:
        recommendation = RECOMMEND_REVIEW
        auto_promote = False
    else:
        recommendation = RECOMMEND_NO_GO
        auto_promote = False

    reason_parts = [f"Score {score}"]
    if compat_score >= 90:
        reason_parts.append("strong domain compatibility")
    elif compat_score < 60:
        reason_parts.append("weak topic-audience match")
    if risk_category != "low":
        reason_parts.append(f"risk: {risk_category}")
    if manual_review:
        reason_parts.append("manual review required")

    return FastValidationResult(
        candidate_id=candidate.id,
        score=score,
        compatibility_score=compat_score,
        specificity_score=specificity,
        audience_clarity_score=audience_score,
        format_fit_score=format_score,
        book_potential_score=book_score,
        evergreen_score=evergreen_score,
        risk_penalty=risk_penalty,
        risk_category=risk_category,
        risk_reason_codes=risk_codes,
        manual_review_required=manual_review or risk_category in ("high", "restricted"),
        auto_promote_allowed=auto_promote,
        recommendation_label=recommendation,
        reason=" | ".join(reason_parts),
        suggested_rewrites=get_rewrite_suggestions(topic_name, audience_name),
    )
