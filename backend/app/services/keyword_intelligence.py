from __future__ import annotations

from dataclasses import dataclass
import re

from app.services.scoring_engine import compute_keyword_specificity_score, keyword_complexity_risk
from app.services.text_utils import normalize_text


AUDIENCE_PATTERNS = [
    ("senior", "Seniorinnen und Senioren"),
    ("anfänger", "Einsteigerinnen und Einsteiger"),
    ("anfanger", "Einsteigerinnen und Einsteiger"),
    ("erwachsene", "Erwachsene"),
    ("kinder", "Kinder"),
    ("frauen", "Frauen"),
    ("männer", "Maenner"),
    ("manner", "Maenner"),
    ("eltern", "Eltern"),
    ("schüler", "Schuelerinnen und Schueler"),
    ("schuler", "Schuelerinnen und Schueler"),
    ("student", "Studierende"),
    ("handwerker", "Handwerkerinnen und Handwerker"),
    ("selbstständig", "Selbststaendige"),
    ("selbststandig", "Selbststaendige"),
    ("betrieb", "Kleine Betriebe"),
    ("pflege", "Pflegende und Angehoerige"),
]

INTENT_FAMILIES = [
    ("tagebuch", "tagebuch"),
    ("logbuch", "logbuch"),
    ("tracker", "tracker"),
    ("planer", "planer"),
    ("journal", "journal"),
    ("arbeitsbuch", "arbeitsbuch"),
    ("übungsbuch", "uebungsbuch"),
    ("ubungsbuch", "uebungsbuch"),
    ("ratgeber", "ratgeber"),
    ("leitfaden", "leitfaden"),
    ("praxisbuch", "praxisbuch"),
    ("handbuch", "handbuch"),
]

CATEGORY_HINTS = [
    (("blutdruck", "blutzucker", "diabetes", "gesund", "medizin", "pflege"), "Gesundheit und Dokumentation"),
    (("adhs", "angst", "trauer", "selbsthilfe", "schattenarbeit"), "Selbsthilfe und mentale Gesundheit"),
    (("haushalt", "familie", "eltern", "schwangerschaft"), "Familie und Alltag"),
    (("lern", "abitur", "prüfung", "prufung", "schule"), "Lernen und Bildung"),
    (("hund", "welpen", "garten", "hobby"), "Hobby und Freizeit"),
    (("handwerk", "nebengewerbe", "kunden", "betrieb", "ki"), "Beruf und Business"),
]


@dataclass(frozen=True)
class KeywordIntelligence:
    target_audience: str | None
    category_hint: str | None
    search_intent_family: str | None
    specificity_score: int
    intent_score: int
    audience_clarity_score: int
    format_suitability_score: int
    competition_probability_score: int
    production_effort_score: int
    risk_level: str


def infer_keyword_intelligence(
    keyword_text: str,
    *,
    book_type: str | None = None,
) -> KeywordIntelligence:
    normalized = normalize_text(keyword_text) or keyword_text
    lowered = normalized.casefold()
    specificity_score = compute_keyword_specificity_score(normalized)
    target_audience = _infer_target_audience_safe(normalized)
    audience_clarity_score = _audience_clarity_score(lowered, target_audience)
    search_intent_family = _intent_family(lowered)
    category_hint = _category_hint(lowered, search_intent_family)
    intent_score = _intent_score(lowered, specificity_score, target_audience)
    format_suitability_score = _format_suitability_score(search_intent_family, book_type, lowered)
    competition_probability_score = _competition_probability_score(lowered, specificity_score, target_audience)
    production_effort_score = _production_effort_score(lowered, book_type, search_intent_family)
    risk_level = _risk_level(lowered)

    return KeywordIntelligence(
        target_audience=target_audience,
        category_hint=category_hint,
        search_intent_family=search_intent_family,
        specificity_score=specificity_score,
        intent_score=intent_score,
        audience_clarity_score=audience_clarity_score,
        format_suitability_score=format_suitability_score,
        competition_probability_score=competition_probability_score,
        production_effort_score=production_effort_score,
        risk_level=risk_level,
    )


def _infer_target_audience(keyword_text: str) -> str | None:
    lowered = keyword_text.casefold()
    if "für " in lowered:
        fragment = keyword_text.split("für ", 1)[1].strip()
        fragment = fragment.split(" mit ", 1)[0].split(" zum ", 1)[0].split(" - ", 1)[0].strip()
        if fragment:
            return fragment[:90]
    for needle, audience in AUDIENCE_PATTERNS:
        if needle in lowered:
            return audience
    return None


def _infer_target_audience_safe(keyword_text: str) -> str | None:
    lowered = keyword_text.casefold()
    match = re.search(r"\b(?:für|fuer)\s+(.+)", keyword_text, flags=re.IGNORECASE)
    if match:
        fragment = match.group(1).strip()
        fragment = fragment.split(" mit ", 1)[0].split(" zum ", 1)[0].split(" - ", 1)[0].strip()
        if fragment:
            return fragment[:90]
    for needle, audience in AUDIENCE_PATTERNS:
        if needle in lowered:
            return audience
    return None


def _intent_family(lowered: str) -> str | None:
    for needle, family in INTENT_FAMILIES:
        if needle in lowered:
            return family
    return None


def _category_hint(lowered: str, intent_family: str | None) -> str | None:
    for needles, category in CATEGORY_HINTS:
        if any(needle in lowered for needle in needles):
            return category
    if intent_family in {"tagebuch", "logbuch", "tracker", "planer", "journal"}:
        return "Low- oder Medium-Content Organisation"
    if intent_family in {"arbeitsbuch", "uebungsbuch", "praxisbuch"}:
        return "Arbeits- und Lernformate"
    if intent_family in {"ratgeber", "leitfaden", "handbuch"}:
        return "Ratgeber und Praxiswissen"
    return None


def _audience_clarity_score(lowered: str, target_audience: str | None) -> int:
    score = 25
    if target_audience:
        score += 35
    if "für " in lowered:
        score += 20
    if any(term in lowered for term, _ in AUDIENCE_PATTERNS):
        score += 15
    return min(100, score)


def _intent_score(lowered: str, specificity_score: int, target_audience: str | None) -> int:
    score = 20 + round(specificity_score * 0.35)
    if target_audience:
        score += 12
    for marker in ["mit", "zum", "für ", "vorlagen", "checklisten", "einfach erklärt", "einfach erklart", "din", "große schrift", "grosse schrift"]:
        if marker in lowered:
            score += 8
    if any(family in lowered for family in ["ratgeber", "leitfaden", "arbeitsbuch", "planer", "tagebuch", "logbuch"]):
        score += 8
    return min(100, score)


def _format_suitability_score(intent_family: str | None, book_type: str | None, lowered: str) -> int:
    score = 45
    if intent_family in {"tagebuch", "logbuch", "tracker", "journal", "planer"}:
        score += 25
    if intent_family in {"arbeitsbuch", "uebungsbuch", "praxisbuch"}:
        score += 30
    if intent_family in {"ratgeber", "leitfaden", "handbuch"}:
        score += 35
    if book_type == "sachbuch" and intent_family in {"ratgeber", "leitfaden", "handbuch", "praxisbuch"}:
        score += 15
    if book_type == "medium_content" and intent_family in {"tagebuch", "planer", "arbeitsbuch", "journal"}:
        score += 15
    if "arbeitsbuch" in lowered and "tagebuch" in lowered:
        score += 8
    return min(100, score)


def _competition_probability_score(lowered: str, specificity_score: int, target_audience: str | None) -> int:
    score = 65
    if specificity_score >= 55:
        score -= 18
    if specificity_score >= 70:
        score -= 10
    if target_audience:
        score -= 10
    if any(token in lowered for token in ["alltag", "senior", "anfänger", "anfanger", "mit", "für "]):
        score -= 8
    if len(lowered.split()) <= 2:
        score += 12
    return max(5, min(100, score))


def _production_effort_score(lowered: str, book_type: str | None, intent_family: str | None) -> int:
    complexity = keyword_complexity_risk(lowered)
    score = 20 + round(complexity * 0.45)
    if book_type == "sachbuch":
        score += 22
    elif book_type == "medium_content":
        score += 10
    if intent_family in {"ratgeber", "leitfaden", "handbuch", "praxisbuch"}:
        score += 16
    elif intent_family in {"arbeitsbuch", "uebungsbuch"}:
        score += 12
    else:
        score += 6
    return max(5, min(100, score))


def _risk_level(lowered: str) -> str:
    risk = keyword_complexity_risk(lowered)
    if risk >= 55:
        return "high"
    if risk >= 30:
        return "medium"
    return "low"
