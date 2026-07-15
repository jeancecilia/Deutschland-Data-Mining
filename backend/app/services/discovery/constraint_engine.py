"""
Constraint Engine — gates which entity combinations are allowed, risky, or blocked.

Prevents nonsense combinations like "Hund + Steuererklärung + Nachtschicht".
"""

from __future__ import annotations

from dataclasses import dataclass

CONSTRAINT_ALLOW = "allow"
CONSTRAINT_BLOCK = "block"
CONSTRAINT_FLAG_RISK = "flag_risk"
CONSTRAINT_DOWNGRADE = "downgrade"


# Global constraint rules: (entity_type_a, entity_type_b) → action
CONSTRAINT_RULES: dict[tuple[str, str], tuple[str, str]] = {
    # Blocks — medical/legal risk areas must not combine with outcome claims
    ("risk_area", "outcome"): (CONSTRAINT_BLOCK, "Keine Ergebnisversprechen bei Risikothemen"),
    ("risk_area", "book_format"): (CONSTRAINT_FLAG_RISK, "Buchformat bei Risikothema prüfen"),

    # Flag risk
    ("problem", "risk_area"): (CONSTRAINT_FLAG_RISK, "Problem + Risikobereich sensibel behandeln"),
    ("life_event", "risk_area"): (CONSTRAINT_FLAG_RISK, "Lebensereignis + Risikobereich vorsichtig"),
    ("audience", "risk_area"): (CONSTRAINT_FLAG_RISK, "Zielgruppe + Risikobereich prüfen"),
    ("profession", "risk_area"): (CONSTRAINT_FLAG_RISK, "Beruf + Risikobereich nur mit Fachautorität"),

    # Explicit allows (positive constraints for clarity)
    ("problem", "audience"): (CONSTRAINT_ALLOW, "Problem + Zielgruppe ist valide"),
    ("problem", "profession"): (CONSTRAINT_ALLOW, "Problem + Beruf ist valide"),
    ("profession", "exam"): (CONSTRAINT_ALLOW, "Beruf + Prüfung ist valide"),
    ("topic", "audience"): (CONSTRAINT_ALLOW, "Thema + Zielgruppe ist valide"),
    ("life_event", "book_format"): (CONSTRAINT_ALLOW, "Lebensereignis + Format ist valide"),
    ("hobby", "book_format"): (CONSTRAINT_ALLOW, "Hobby + Format ist valide"),
    ("object", "book_format"): (CONSTRAINT_ALLOW, "Objekt + Format ist valide"),
    ("skill", "profession"): (CONSTRAINT_ALLOW, "Skill + Beruf ist valide"),
    ("skill", "audience"): (CONSTRAINT_ALLOW, "Skill + Zielgruppe ist valide"),

    # Downgrades — too broad combinations
    ("topic", "topic"): (CONSTRAINT_DOWNGRADE, "Zwei Topics ohne Zielgruppe zu breit"),
    ("object", "object"): (CONSTRAINT_DOWNGRADE, "Zwei Objekte ohne Kontext schwach"),
    ("audience", "audience"): (CONSTRAINT_DOWNGRADE, "Zwei Zielgruppen ohne Problem unklar"),
}


# Generic / banned phrases that indicate a too-broad topic
GENERIC_BANNED_PHRASES = {
    "glück", "glueck", "gesundheit", "geld", "erfolg", "leben",
    "fitness", "gesund", "einfach", "schnell", "besser",
    "hilfe", "tipps", "tricks", "guide", "buch",
}

# Minimum specificity requirements
MIN_CANDIDATE_WORDS = 3  # At least 3 words in candidate phrase


@dataclass(frozen=True)
class ConstraintCheckResult:
    allowed: bool
    action: str  # allow, block, flag_risk, downgrade
    reason: str
    entity_types_involved: list[str]


def check_constraint(
    entity_types_a: list[str],
    entity_types_b: list[str],
) -> ConstraintCheckResult:
    """Check if two sets of entity types can be combined.

    Evaluates all pairs and returns the most restrictive result found.
    Severity: block > flag_risk > downgrade > allow
    """
    SEVERITY = {
        CONSTRAINT_BLOCK: 4,
        CONSTRAINT_FLAG_RISK: 3,
        CONSTRAINT_DOWNGRADE: 2,
        CONSTRAINT_ALLOW: 1,
    }

    best_result = ConstraintCheckResult(
        allowed=True,
        action=CONSTRAINT_ALLOW,
        reason="Keine Restriktion gefunden",
        entity_types_involved=entity_types_a + entity_types_b,
    )
    best_severity = SEVERITY[CONSTRAINT_ALLOW]

    for type_a in entity_types_a:
        for type_b in entity_types_b:
            key = (type_a, type_b)
            if key in CONSTRAINT_RULES:
                action, reason = CONSTRAINT_RULES[key]
                severity = SEVERITY.get(action, 0)
                if severity > best_severity:
                    best_result = ConstraintCheckResult(
                        allowed=(action != CONSTRAINT_BLOCK),
                        action=action,
                        reason=reason,
                        entity_types_involved=[type_a, type_b],
                    )
                    best_severity = severity
                    if action == CONSTRAINT_BLOCK:
                        return best_result  # block is absolute, return early

    return best_result


def is_too_generic(phrase: str) -> bool:
    """Check if a candidate phrase is too generic to be a valid KDP niche."""
    lowered = phrase.casefold()
    tokens = lowered.split()

    # Too few content words
    if len(tokens) < MIN_CANDIDATE_WORDS:
        return True

    # Contains only banned/generic phrases
    meaningful = [t for t in tokens if t not in GENERIC_BANNED_PHRASES and len(t) > 2]
    if len(meaningful) < 2:
        return True

    # Phrase is just a single broad concept
    if len(tokens) <= 2 and any(t in GENERIC_BANNED_PHRASES for t in tokens):
        return True

    return False


def get_risk_level(entity_types: list[str]) -> str:
    """Determine overall risk level of a combination."""
    if "risk_area" in entity_types:
        return "high"
    high_risk_types = {"problem", "life_event"}
    if any(t in high_risk_types for t in entity_types) and "audience" not in entity_types:
        return "medium"
    return "low"


constraint_engine = check_constraint
