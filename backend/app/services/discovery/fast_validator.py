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
from app.services.discovery.candidate_quality_gate import evaluate_candidate_quality

@dataclass(frozen=True)
class FastValidationResult:
    candidate_id: int
    score: int
    compatibility_score: int
    specificity_score: int
    format_fit_score: int
    risk_category: str
    risk_reason_codes: list[str] = field(default_factory=list)
    manual_review_required: bool = False
    auto_promote_allowed: bool = False
    recommendation_label: str = "REVIEW_REQUIRED"
    reason: str = ""


def validate_candidates_fast(
    db: Session,
    *,
    limit: int = 100,
) -> list[FastValidationResult]:
    """Fast-validate new niche candidates using the central quality gate."""
    candidates = list(
        db.scalars(
            select(NicheCandidate)
            .where(NicheCandidate.status == "prevalidation_queued")
            .order_by(NicheCandidate.confidence.desc())
            .limit(limit)
        )
    )

    # Load entity names for resolution
    entity_map: dict[int, str] = {}
    for e in db.scalars(select(DiscoveryEntity)):
        entity_map[e.id] = e.name

    results: list[FastValidationResult] = []
    for candidate in candidates:
        # Resolve entity names
        topic_name = entity_map.get(candidate.main_topic_entity_id) if candidate.main_topic_entity_id else None
        audience_name = entity_map.get(candidate.audience_entity_id) if candidate.audience_entity_id else None
        problem_name = entity_map.get(candidate.problem_entity_id) if candidate.problem_entity_id else None
        format_name = entity_map.get(candidate.format_entity_id) if candidate.format_entity_id else None
        
        meta = candidate.source_entities or {}

        gate_result = evaluate_candidate_quality(
            candidate_name=candidate.candidate_name,
            topic_name=topic_name,
            audience_name=audience_name,
            problem_name=problem_name,
            format_name=format_name,
            meta=meta,
        )
        
        manual_review = gate_result.risk_category in ("high", "restricted") or gate_result.recommendation == "MAYBE"
        auto_promote = gate_result.recommendation == "GO"

        result = FastValidationResult(
            candidate_id=candidate.id,
            score=gate_result.total_score,
            compatibility_score=gate_result.compatibility_score,
            specificity_score=gate_result.specificity_score,
            format_fit_score=gate_result.format_score,
            risk_category=gate_result.risk_category,
            risk_reason_codes=gate_result.reason_codes,
            manual_review_required=manual_review,
            auto_promote_allowed=auto_promote,
            recommendation_label=gate_result.recommendation,
            reason=gate_result.reason,
        )

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

        # Set status
        if result.recommendation_label == "BLOCKED":
            candidate.status = "blocked"
            candidate.rejection_reason = result.reason
        elif result.recommendation_label == "NO-GO":
            candidate.status = "rejected"
            candidate.rejection_reason = result.reason
        elif result.recommendation_label in ("MAYBE", "REVIEW_REQUIRED"):
            candidate.status = "needs_manual_review"
            candidate.promotion_reason = result.reason
        elif result.auto_promote_allowed and result.recommendation_label == "GO":
            candidate.status = "fast_validated"
            candidate.promotion_reason = result.reason
        else:
            candidate.status = "needs_manual_review"
            candidate.promotion_reason = result.reason

        db.add(candidate)
        results.append(result)

    db.commit()
    return results
