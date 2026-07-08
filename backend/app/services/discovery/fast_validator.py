"""
Fast Validator — inexpensive pre-validation of niche candidates before deep KDP analysis.

Checks specificity, audience clarity, problem clarity, format fit,
book potential, evergreen potential, and risk — all without Amazon API calls.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import NicheCandidate


RECOMMEND_REJECT = "reject"
RECOMMEND_MANUAL_REVIEW = "manual_review"
RECOMMEND_PROMOTE = "promote_to_seed"
RECOMMEND_KEYWORD_EXPANSION = "send_to_keyword_expansion"
RECOMMEND_SACHBUCH = "send_to_sachbuch_pipeline"

# Word patterns that indicate good KDP potential
STRONG_AUDIENCE_WORDS = {
    "für", "senioren", "anfänger", "einsteiger", "eltern", "kinder",
    "schüler", "studenten", "selbstständige", "handwerker", "pflegekräfte",
    "berufstätige", "alleinerziehende", "schichtarbeiter",
}

STRONG_PROBLEM_WORDS = {
    "stress", "angst", "schmerz", "überforderung", "organisation",
    "struktur", "planung", "dokumentation", "bewältigung",
    "management", "training", "routine",
}

STRONG_FORMAT_WORDS = {
    "tagebuch", "planer", "workbook", "checkliste", "ratgeber",
    "leitfaden", "arbeitsbuch", "logbuch", "tracker", "journal",
    "lernplaner", "übungsbuch",
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
    specificity_score: int
    audience_clarity_score: int
    problem_clarity_score: int
    format_fit_score: int
    book_potential_score: int
    evergreen_score: int
    risk_penalty: int
    recommended_action: str
    reason: str


def validate_candidates_fast(
    db: Session,
    *,
    limit: int = 100,
) -> list[FastValidationResult]:
    """Fast-validate new niche candidates.

    Only processes candidates with status='new'.
    Updates fast_validation_score, status, rejection_reason, promotion_reason.
    """
    candidates = list(
        db.scalars(
            select(NicheCandidate)
            .where(NicheCandidate.status == "new")
            .order_by(NicheCandidate.confidence.desc())
            .limit(limit)
        )
    )

    results: list[FastValidationResult] = []
    for candidate in candidates:
        result = _validate_one(candidate)
        results.append(result)

        # Update candidate
        candidate.fast_validation_score = result.score

        if result.recommended_action == RECOMMEND_REJECT:
            candidate.status = "rejected"
            candidate.rejection_reason = result.reason
        elif result.recommended_action == RECOMMEND_PROMOTE:
            candidate.status = "fast_validated"  # ready for promotion
            candidate.promotion_reason = result.reason
        elif result.recommended_action == RECOMMEND_MANUAL_REVIEW:
            candidate.status = "needs_manual_review"
        else:
            candidate.status = "fast_validated"

        db.add(candidate)

    db.commit()
    return results


def _validate_one(candidate: NicheCandidate) -> FastValidationResult:
    phrase = candidate.candidate_name.casefold()

    # Specificity (0-100)
    word_count = len(phrase.split())
    specificity = min(100, max(10, word_count * 18))
    if word_count >= 5:
        specificity += 10
    if "für" in phrase:
        specificity += 8

    # Audience clarity (0-100)
    audience_score = 20
    if any(w in phrase for w in STRONG_AUDIENCE_WORDS):
        audience_score = min(100, audience_score + 40)
    if candidate.audience_entity_id:
        audience_score = min(100, audience_score + 30)

    # Problem clarity (0-100)
    problem_score = 15
    if any(w in phrase for w in STRONG_PROBLEM_WORDS):
        problem_score = min(100, problem_score + 45)
    if candidate.problem_entity_id:
        problem_score = min(100, problem_score + 35)

    # Format fit (0-100)
    format_score = 30
    if any(w in phrase for w in STRONG_FORMAT_WORDS):
        format_score = min(100, format_score + 40)
    if candidate.format_entity_id:
        format_score = min(100, format_score + 30)

    # Book potential (0-100) — could this be a real book?
    book_score = 25
    if candidate.book_class_guess == "sachbuch":
        book_score += 30
    elif candidate.book_class_guess == "medium_content":
        book_score += 20
    if audience_score >= 50 and problem_score >= 50:
        book_score += 20
    if word_count >= 4:
        book_score += 10
    # Penalize too-broad
    if word_count <= 2:
        book_score -= 20

    # Evergreen (0-100)
    evergreen_score = 20
    if any(w in phrase for w in EVERGREEN_SIGNALS):
        evergreen_score = min(100, evergreen_score + 40)
    if candidate.risk_level == "low":
        evergreen_score += 15

    # Risk penalty (0-60)
    risk_penalty = 0
    if candidate.risk_level == "high":
        risk_penalty = 45
    elif candidate.risk_level == "medium":
        risk_penalty = 20
    # Sensitive topics
    sensitive = {"medizin", "gesundheit", "therapie", "recht", "steuer", "investment"}
    if any(w in phrase for w in sensitive):
        risk_penalty = max(risk_penalty, 30)

    # Final score
    score = max(0, min(100, (
        specificity * 0.18
        + audience_score * 0.18
        + problem_score * 0.16
        + format_score * 0.14
        + book_score * 0.20
        + evergreen_score * 0.14
        - risk_penalty * 0.12
    )))

    # Recommendation
    if score >= 65:
        action = RECOMMEND_PROMOTE
        reason = f"Score {score}: gute Spezifität ({specificity}), Zielgruppenklarheit ({audience_score}), Buchpotenzial ({book_score})"
    elif score >= 45:
        action = RECOMMEND_MANUAL_REVIEW
        reason = f"Score {score}: mittlere Bewertung, manuelle Prüfung empfohlen"
    elif score >= 25:
        if candidate.book_class_guess == "sachbuch":
            action = RECOMMEND_SACHBUCH
            reason = f"Score {score}: könnte als Sachbuch funktionieren, tiefer prüfen"
        else:
            action = RECOMMEND_MANUAL_REVIEW
            reason = f"Score {score}: grenzwertig"
    else:
        action = RECOMMEND_REJECT
        reason = f"Score {score}: zu niedrige Spezifität ({specificity}) oder Buchpotenzial ({book_score})"

    return FastValidationResult(
        candidate_id=candidate.id,
        score=score,
        specificity_score=specificity,
        audience_clarity_score=audience_score,
        problem_clarity_score=problem_score,
        format_fit_score=format_score,
        book_potential_score=book_score,
        evergreen_score=evergreen_score,
        risk_penalty=risk_penalty,
        recommended_action=action,
        reason=reason,
    )
