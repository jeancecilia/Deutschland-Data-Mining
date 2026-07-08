"""
Domain Compatibility Rules — curated maps of valid and invalid entity combinations.

These rules encode domain knowledge about which topics, audiences, problems,
and formats actually belong together in the German KDP market.
"""

from __future__ import annotations

# ── Compatible pairs: (topic_key, audience_key) ──────────────────────────
# Keys are normalized lowercase versions of entity names.

DOMAIN_AUDIENCE_COMPATIBILITY: dict[str, list[str]] = {
    "ki im handwerk": [
        "handwerker", "kleinunternehmer", "selbstständige", "betriebe",
        "dienstleister", "kleine betriebe", "solo-selbstständige",
        "elektriker", "tischler", "installateur", "maler",
    ],
    "pflege": [
        "pflegekräfte", "angehörige", "senioren", "pflegebedürftige",
        "familien", "pflegende", "krankenpfleger", "krankenschwester",
        "pflegefachfrau", "pflegefachmann", "altenpfleger",
    ],
    "pflegegrad": [
        "senioren", "angehörige", "pflegebedürftige", "familien",
        "rentner", "ruheständler",
    ],
    "pflegeantrag": [
        "senioren", "angehörige", "pflegebedürftige", "familien",
        "rentner", "ruheständler",
    ],
    "pflegebedürftigkeit": [
        "senioren", "angehörige", "pflegebedürftige", "familien",
        "pflegekräfte", "rentner",
    ],
    "pflegeorganisation": [
        "pflegekräfte", "angehörige", "familien", "pflegedienstleister",
    ],
    "steuererklärung": [
        "selbstständige", "freelancer", "kleinunternehmer", "rentner",
        "arbeitnehmer", "gründer",
    ],
    "buchhaltung": [
        "selbstständige", "freelancer", "kleinunternehmer", "gründer",
    ],
    "adhs": [
        "erwachsene mit adhs", "eltern", "kinder", "studenten",
        "berufstätige", "schüler", "studierende", "lehrer",
    ],
    "alleinerziehend": [
        "alleinerziehende", "eltern", "mütter", "väter", "familien",
    ],
    "alleinerziehend alltag": [
        "alleinerziehende", "eltern", "mütter", "väter",
    ],
    "eltern": [
        "eltern", "familien", "kinder", "alleinerziehende",
        "großeltern", "angehörige",
    ],
    "demenz": [
        "senioren", "angehörige", "pflegekräfte", "pflegende",
        "rentner", "ruheständler", "familien",
    ],
    "blutdruck": [
        "senioren", "angehörige", "patienten", "erwachsene",
    ],
    "blutzucker": [
        "senioren", "diabetiker", "angehörige", "patienten",
    ],
    "ernährung": [
        "senioren", "sportler", "berufstätige", "familien",
        "schichtarbeiter", "studenten", "anfänger",
    ],
    "fitness": [
        "anfänger", "berufstätige", "senioren", "sportler",
        "frauen", "männer",
    ],
    "hund": [
        "hundehalter", "hundebesitzer", "familien", "anfänger",
    ],
    "hundetraining": [
        "hundehalter", "hundebesitzer", "anfänger",
    ],
    "welpen": [
        "hundehalter", "hundebesitzer", "familien", "anfänger",
    ],
    "garten": [
        "anfänger", "hausbesitzer", "senioren", "hobbygärtner",
    ],
    "kochen": [
        "anfänger", "familien", "berufstätige", "studenten",
        "singles", "senioren",
    ],
    "yoga": [
        "anfänger", "frauen", "senioren", "berufstätige",
        "sportler", "schwangere",
    ],
    "chatgpt": [
        "selbstständige", "studenten", "senioren", "lehrer",
        "anfänger", "berufstätige",
    ],
    "ki": [
        "selbstständige", "handwerker", "kleinunternehmer", "lehrer",
        "studenten", "anfänger", "berufstätige",
    ],
    "excel": [
        "selbstständige", "studenten", "berufstätige", "anfänger",
        "bürokaufmann", "kleinunternehmer",
    ],
    "haushalt": [
        "familien", "alleinerziehende", "berufstätige", "anfänger",
        "erwachsene mit adhs", "studenten",
    ],
    "lernorganisation": [
        "studenten", "schüler", "studierende", "erwachsene mit adhs",
        "eltern", "lehrer",
    ],
    "renovierung": [
        "hausbesitzer", "heimwerker", "anfänger", "selbstständige",
    ],
    "umzug": [
        "familien", "berufstätige", "studenten", "singles",
    ],
    "hochzeit": [
        "paare", "brautpaare", "frauen",
    ],
    "schwangerschaft": [
        "frauen", "mütter", "eltern", "paare",
    ],
    "rente": [
        "rentner", "ruheständler", "senioren",
    ],
    "bewerbung": [
        "studenten", "berufstätige", "arbeitnehmer", "absolventen",
    ],
    "selbstständigkeit": [
        "gründer", "freelancer", "kleinunternehmer", "handwerker",
    ],
    "existenzgründung": [
        "gründer", "selbstständige", "kleinunternehmer",
    ],
    "fotografie": [
        "anfänger", "hobbyfotografen", "einsteiger",
    ],
    "nähen": [
        "anfänger", "hobby-schneiderinnen", "einsteiger",
    ],
    "stricken": [
        "anfänger", "hobby-strickerinnen", "einsteiger",
    ],
    "programmieren": [
        "anfänger", "studenten", "berufseinsteiger", "quereinsteiger",
    ],
    "angeln": [
        "angler", "anfänger", "hobbyangler",
    ],
    "camping": [
        "familien", "paare", "anfänger", "camper",
    ],
    "wandern": [
        "anfänger", "senioren", "familien", "naturfreunde",
    ],
    "backen": [
        "anfänger", "familien", "hobbybäcker",
    ],
}


# ── Incompatible pairs: (topic_key, audience_key) ────────────────────────
INCOMPATIBLE_COMBINATIONS: set[tuple[str, str]] = {
    # Handwerk topics don't go with non-handwerk audiences
    ("ki im handwerk", "pflege"),
    ("ki im handwerk", "pflegekräfte"),
    ("ki im handwerk", "pflegefachfrau"),
    ("ki im handwerk", "rentner"),
    ("ki im handwerk", "ruheständler"),
    ("ki im handwerk", "senioren"),
    ("ki im handwerk", "angehörige"),
    ("ki im handwerk", "erwachsene mit adhs"),
    ("ki im handwerk", "eltern"),
    ("ki im handwerk", "alleinerziehende"),

    # Pflege topics don't go with business audiences
    ("pflegegrad", "kleinunternehmer"),
    ("pflegegrad", "selbstständige"),
    ("pflegegrad", "freelancer"),
    ("pflegegrad", "handwerker"),
    ("pflegebedürftigkeit", "freelancer"),
    ("pflegebedürftigkeit", "kleinunternehmer"),
    ("pflegebedürftigkeit", "selbstständige"),
    ("pflegebedürftigkeit", "handwerker"),
    ("pflegeantrag", "kleinunternehmer"),
    ("pflegeantrag", "freelancer"),
    ("pflegeantrag", "selbstständige"),
    ("pflegeantrag", "handwerker"),
    ("pflege", "kleinunternehmer"),
    ("pflege", "handwerker"),

    # Family topics don't go with senior/business audiences
    ("alleinerziehend alltag", "ruheständler"),
    ("alleinerziehend alltag", "rentner"),
    ("alleinerziehend alltag", "freelancer"),
    ("alleinerziehend alltag", "kleinunternehmer"),
    ("alleinerziehend alltag", "handwerker"),
    ("alleinerziehend", "ruheständler"),
    ("alleinerziehend", "rentner"),
    ("alleinerziehend", "freelancer"),

    ("eltern", "pflege"),
    ("eltern", "ruheständler"),
    ("eltern", "rentner"),
    ("eltern", "freelancer"),
    ("eltern", "kleinunternehmer"),
    ("eltern", "handwerker"),

    # Senior topics don't go with non-senior audiences
    ("rente", "freelancer"),
    ("rente", "kleinunternehmer"),
    ("rente", "handwerker"),
    ("rente", "studenten"),
    ("demenz", "freelancer"),
    ("demenz", "kleinunternehmer"),
    ("demenz", "handwerker"),

    # Hobby topics with wrong audiences
    ("hund", "kleinunternehmer"),
    ("hund", "freelancer"),
    ("hund", "handwerker"),
    ("garten", "freelancer"),
    ("garten", "kleinunternehmer"),

    # Business topics with wrong audiences
    ("buchhaltung", "senioren"),
    ("buchhaltung", "ruheständler"),
    ("buchhaltung", "rentner"),
    ("buchhaltung", "pflegekräfte"),
    ("steuererklärung", "pflegekräfte"),
    ("steuererklärung", "schüler"),
    ("existenzgründung", "rentner"),
    ("existenzgründung", "ruheständler"),
    ("selbstständigkeit", "rentner"),
    ("selbstständigkeit", "schüler"),

    # Skill/tool with wrong audiences
    ("excel", "pflegekräfte"),
    ("excel", "senioren"),
    ("excel", "handwerker"),
    ("programmieren", "pflegekräfte"),
    ("programmieren", "handwerker"),

    # Hobby audience mismatches
    ("stricken", "handwerker"),
    ("stricken", "kleinunternehmer"),
    ("nähen", "handwerker"),
    ("nähen", "kleinunternehmer"),
    ("fotografie", "pflegekräfte"),
    ("fotografie", "handwerker"),

    # Life event mismatches
    ("schwangerschaft", "senioren"),
    ("schwangerschaft", "rentner"),
    ("hochzeit", "pflegekräfte"),
    ("hochzeit", "handwerker"),
    ("bewerbung", "rentner"),
    ("bewerbung", "ruheständler"),
    ("bewerbung", "pflegekräfte"),
}


# ── Risk classification rules ─────────────────────────────────────────────

# Words that indicate health/medical risk
HEALTH_RISK_WORDS = {
    "medizin", "gesundheit", "therapie", "behandlung", "diagnose",
    "symptom", "erkrankung", "krankheit", "heilung", "blutdruck",
    "blutzucker", "diabetes", "demenz", "alzheimer", "adhs",
    "depression", "angststörung", "neurofeedback", "hormon",
    "anabol", "steroide", "doping", "testosteron",
}

# Words that indicate legal risk
LEGAL_RISK_WORDS = {
    "recht", "gesetz", "steuer", "vertrag", "klage", "anwalt",
    "gericht", "straf", "haftung", "urteil", "einklagen",
}

# Words that indicate financial risk
FINANCIAL_RISK_WORDS = {
    "investment", "aktien", "trading", "krypto", "bitcoin",
    "geldanlage", "rendite", "gewinn", "reich", "passives einkommen",
    "finanzielle freiheit",
}

# Words that indicate substance/drug risk
SUBSTANCE_RISK_WORDS = {
    "steroide", "anabol", "doping", "testosteron", "hormon",
    "dosierung", "zyklus", "cycle", "kur", "substanz",
}

# Words that should be BLOCKED entirely
BLOCKED_WORDS = {
    "dosierungsplan", "cycle", "dosis", "einnahmeplan",
    "beschaffung", "quelle", "bezugsquelle", "darknet",
    "illegal", "straftat", "umgehung", "hinterziehung",
}


def classify_risk(phrase: str, topic: str | None = None) -> tuple[str, list[str], bool]:
    """Classify a candidate phrase into risk levels.

    Returns: (risk_category, reason_codes, manual_review_required)
    """
    lowered = phrase.casefold()
    risk_category = "low"
    reason_codes: list[str] = []
    manual_review_required = False

    # Check blocked words first
    if any(w in lowered for w in BLOCKED_WORDS):
        return ("blocked", ["blocked_content"], True)

    # Check substance risk
    if any(w in lowered for w in SUBSTANCE_RISK_WORDS):
        risk_category = "high"
        reason_codes.append("substance_related")
        reason_codes.append("expert_review_required")
        manual_review_required = True
        # Check if it's educational vs instructional
        if any(w in lowered for w in {"dosierung", "zyklus", "cycle", "kur", "plan", "einnahme"}):
            risk_category = "restricted"
            reason_codes.append("dosage_content")

    # Check health risk
    health_hits = [w for w in HEALTH_RISK_WORDS if w in lowered]
    if health_hits:
        if risk_category == "low":
            risk_category = "high"
        reason_codes.append("health_sensitive")
        reason_codes.append("expert_review_required")
        manual_review_required = True

    # Check legal risk
    legal_hits = [w for w in LEGAL_RISK_WORDS if w in lowered]
    if legal_hits:
        if risk_category in ("low", "medium"):
            risk_category = "high"
        reason_codes.append("legal_sensitive")
        manual_review_required = True

    # Check financial risk
    financial_hits = [w for w in FINANCIAL_RISK_WORDS if w in lowered]
    if financial_hits:
        if risk_category in ("low", "medium"):
            risk_category = "high"
        reason_codes.append("financial_sensitive")
        manual_review_required = True

    # Medium risk: common sensitive but manageable topics
    medium_triggers = {"bewerbung", "karriere", "erziehung", "pflegeorganisation",
                       "alltagsgesundheit", "fitness", "ernährung", "produktivität"}
    if risk_category == "low" and any(w in lowered for w in medium_triggers):
        risk_category = "medium"

    if not reason_codes and risk_category == "low":
        reason_codes.append("no_risk_detected")

    return (risk_category, reason_codes, manual_review_required)
