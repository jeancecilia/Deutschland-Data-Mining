"""
Candidate Quality Gate — single source of truth for candidate evaluation.

Used by generators, rankers, and validators to strictly enforce semantic 
compatibility, calculate format/specificity scores, and reject bad combinations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from app.services.discovery.semantic_compatibility import check_semantic_compatibility
from app.services.discovery.domain_compatibility_rules import classify_risk
from app.services.discovery.format_fit_rules import score_format_fit

@dataclass(frozen=True)
class CandidateQualityResult:
    allowed: bool
    hard_block: bool
    compatibility_score: int
    format_score: int
    specificity_score: int
    reason_codes: list[str]
    reason: str
    total_score: int
    risk_category: str
    recommendation: str

STRONG_FORMAT_WORDS = {
    "tagebuch", "planer", "workbook", "checkliste", "ratgeber",
    "leitfaden", "arbeitsbuch", "logbuch", "tracker", "journal",
    "lernplaner", "übungsbuch", "praxisbuch", "handbuch",
    "trainingsbuch", "kochbuch",
}

CONCRETE_USE_CASE_WORDS = {
    "blutdruckwerte", "pflegegrad", "antrag", "rückruftraining",
    "hundebegegnungen", "steuerunterlagen", "belege", "rechnungen",
    "umzugscheckliste", "haushaltsbudget", "smartphone", "excel",
    "lebenslauf", "vorstellungsgespräch", "medikamentenplan",
    "blutdruck", "blutzucker", "diabetes", "demenz", "adhs",
    "buchhaltung", "steuererklärung", "bewerbung", "kündigung",
    "mietvertrag", "arbeitsvertrag", "rechnung", "fotografie",
    "programmieren", "kochen", "backen", "garten", "fitness",
    "yoga", "meditation", "sprache", "vokabeln", "grammatik",
    "führerschein", "prüfung", "abitur", "studium",
}

def evaluate_candidate_quality(
    *,
    candidate_name: str,
    topic_name: str | None,
    audience_name: str | None,
    problem_name: str | None,
    format_name: str | None,
    meta: dict | None = None,
) -> CandidateQualityResult:
    phrase = candidate_name.casefold()
    reasons = []
    reason_codes = []
    
    # 1. Semantic Compatibility (Most Important)
    compat = check_semantic_compatibility(topic_name, audience_name, problem_name, format_name)
    compat_score = compat.score
    
    if compat.hard_block:
        return CandidateQualityResult(
            allowed=False,
            hard_block=True,
            compatibility_score=compat_score,
            format_score=0,
            specificity_score=0,
            reason_codes=["semantic_mismatch"],
            reason=f"Semantic mismatch: {compat.reason}",
            total_score=0,
            risk_category="low",
            recommendation="NO-GO",
        )
        
    # 2. Risk Classification
    risk_category, risk_codes, manual_review = classify_risk(phrase, topic_name)
    reason_codes.extend(risk_codes)
    
    risk_penalty = 0
    if risk_category == "blocked":
        return CandidateQualityResult(
            allowed=False,
            hard_block=True,
            compatibility_score=compat_score,
            format_score=0,
            specificity_score=0,
            reason_codes=reason_codes + ["blocked_content"],
            reason="Blocked: contains prohibited content indicators",
            total_score=0,
            risk_category="blocked",
            recommendation="BLOCKED",
        )
    elif risk_category == "restricted":
        risk_penalty = 50
    elif risk_category == "high":
        risk_penalty = 30
    elif risk_category == "medium":
        risk_penalty = 10
        
    # 3. Format Score
    macro = str(meta.get("macro_domain", meta.get("domain", ""))).lower() if meta else None
    sub = str(meta.get("subdomain", "")).lower() if meta else None
    
    format_score = score_format_fit(candidate_name, macro, sub)
    if any(w in phrase for w in STRONG_FORMAT_WORDS):
        format_score = min(100, format_score + 25)
        
    # 4. Specificity Score
    word_count = len(phrase.split())
    specificity = min(100, max(20, word_count * 15))
    if "für" in phrase:
        specificity += 10
    if any(cw in phrase for cw in CONCRETE_USE_CASE_WORDS):
        specificity += 20
    else:
        specificity -= 20
        
    # Penalties and Boosts
    if compat_score < 40:
        specificity = max(0, specificity - 30)
    if compat_score >= 75:
        specificity = min(100, specificity + 10)
        
    # Final Total Score
    total_score = max(0, min(100, int(
        compat_score * 0.40
        + specificity * 0.35
        + format_score * 0.25
        - risk_penalty
    )))
    
    # Recommendation Logic
    allowed = total_score >= 65
    hard_block = False
    
    if risk_category in ("restricted", "blocked"):
        recommendation = "BLOCKED"
        allowed = False
        hard_block = True
    elif total_score >= 75:
        recommendation = "GO"
    elif total_score >= 65:
        recommendation = "MAYBE"
    else:
        recommendation = "NO-GO"
        hard_block = True
        
    if compat_score < 60:
        reasons.append("weak topic-audience match")
    if risk_category != "low":
        reasons.append(f"risk: {risk_category}")
    if total_score < 65:
        reasons.append(f"low quality score ({total_score})")
        
    reason_str = " | ".join(reasons) if reasons else f"Score {total_score}"
    
    return CandidateQualityResult(
        allowed=allowed,
        hard_block=hard_block,
        compatibility_score=compat_score,
        format_score=format_score,
        specificity_score=specificity,
        reason_codes=reason_codes,
        reason=reason_str,
        total_score=total_score,
        risk_category=risk_category,
        recommendation=recommendation,
    )
