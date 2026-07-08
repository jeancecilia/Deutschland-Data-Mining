from __future__ import annotations

from dataclasses import dataclass

from app.services.text_utils import normalize_text


MAX_EXPANSIONS = 180

GENERIC_AUDIENCES = [
    "für Anfänger",
    "für Einsteiger",
    "für Erwachsene",
    "für Senioren",
    "für Frauen",
    "für Männer",
    "für Familien",
    "für Eltern",
    "für Berufstätige",
    "für Selbstständige",
]

GENERIC_FEATURES = [
    "mit Checklisten",
    "mit Vorlagen",
    "mit Beispielen",
    "mit Übungen",
    "mit Reflexionsfragen",
    "mit Monatsübersicht",
    "mit Wochenübersicht",
    "mit Auswertung",
    "mit Schritt-für-Schritt-Anleitung",
    "einfach erklärt",
]

GENERIC_USE_CASES = [
    "für den Alltag",
    "für zu Hause",
    "für unterwegs",
    "für die Praxis",
    "für den Beruf",
    "zur Selbstorganisation",
    "zur Dokumentation",
    "zum Ausfüllen",
    "zum Nachschlagen",
    "zum Verschenken",
]

GENERIC_FORMAT_VARIANTS = [
    "DIN A4",
    "DIN A5",
    "große Schrift",
    "kompakt",
    "übersichtlich",
    "minimalistisch",
]

INTENT_CONFIG = {
    "tagebuch": {
        "replacements": ["Tagebuch", "Logbuch", "Tracker", "Journal"],
        "features": [
            "mit Platz zum Schreiben",
            "mit Trendseiten",
            "mit Notizfeldern",
            "mit Tagesübersicht",
            "mit Wochenrückblick",
            "für Arztbesuche",
        ],
    },
    "planer": {
        "replacements": ["Planer", "Wochenplaner", "Tagesplaner", "Organisationsplaner"],
        "features": [
            "mit Routinen",
            "mit Wochenzielen",
            "mit Monatsplanung",
            "für Termine",
            "für Fokus und Struktur",
            "mit Prioritätenlisten",
        ],
    },
    "journal": {
        "replacements": ["Journal", "Tagebuch", "Arbeitsbuch", "Reflexionsbuch"],
        "features": [
            "mit Reflexion",
            "mit Fragen",
            "für jeden Tag",
            "mit Impulsen",
            "für Morgen- und Abendroutine",
            "mit Dankbarkeitsseiten",
        ],
    },
    "logbuch": {
        "replacements": ["Logbuch", "Nachweisbuch", "Dokumentationsbuch", "Eintragbuch"],
        "features": [
            "für Nachweise",
            "für Kontrollen",
            "für Dokumentation",
            "mit Prüfprotokollen",
            "mit Unterschriftsfeldern",
            "mit Übersichtstabellen",
        ],
    },
    "arbeitsbuch": {
        "replacements": ["Arbeitsbuch", "Übungsbuch", "Praxisbuch", "Begleitbuch"],
        "features": [
            "mit Übungen",
            "mit Aufgaben",
            "Schritt für Schritt",
            "für Selbsthilfe",
            "mit Praxisbeispielen",
            "mit Worksheets",
        ],
    },
    "ratgeber": {
        "replacements": ["Ratgeber", "Praxisratgeber", "Leitfaden", "Handbuch"],
        "features": [
            "einfach erklärt",
            "mit Beispielen",
            "mit Praxiswissen",
            "für Deutschland",
            "aktuell",
            "mit Checklisten",
        ],
    },
}

TOPIC_TAILS = [
    (
        ("blutdruck", "blutzucker", "diabetes", "gesundheit", "pflege"),
        [
            "mit Werten und Notizen",
            "mit Medikamentenplan",
            "für Arzttermine",
            "für Pflege zu Hause",
            "für Angehörige",
            "bei Bluthochdruck",
            "mit Tageswerten",
            "mit Wochenauswertung",
        ],
    ),
    (
        ("adhs", "angst", "trauer", "selbsthilfe", "schattenarbeit"),
        [
            "für mehr Struktur",
            "für emotionale Klarheit",
            "für Routinen",
            "für den Alltag",
            "mit Reflexionsseiten",
            "mit Übungen zur Selbsthilfe",
            "mit Fokus-Planung",
            "mit Wochenreflexion",
        ],
    ),
    (
        ("haushalt", "familie", "eltern", "schwangerschaft"),
        [
            "für Familien",
            "für den Familienalltag",
            "für werdende Eltern",
            "mit Planungsseiten",
            "mit Checklisten für den Alltag",
            "für Organisation zu Hause",
            "mit Wochenplanung",
            "mit Routinen",
        ],
    ),
    (
        ("lern", "abitur", "prüfung", "schule", "studium"),
        [
            "für die Prüfungsvorbereitung",
            "mit Lernplan",
            "mit Wochenzielen",
            "für Schüler",
            "für Studierende",
            "mit Wiederholungsplan",
            "mit Fortschrittstracker",
            "mit Lernmethoden",
        ],
    ),
    (
        ("hund", "welpen", "garten", "hobby"),
        [
            "für Anfänger",
            "für den Alltag",
            "mit Schritt-für-Schritt-Plan",
            "mit Checklisten",
            "mit Praxisbeispielen",
            "für zu Hause",
            "für Training und Routinen",
            "mit Wochenplan",
        ],
    ),
    (
        ("handwerk", "handwerker", "nebengewerbe", "betrieb", "kunden", "ki"),
        [
            "für kleine Betriebe",
            "für Selbstständige",
            "für den Betriebsalltag",
            "mit Vorlagen für Kundenkommunikation",
            "mit Praxisbeispielen aus Deutschland",
            "für mehr Effizienz",
            "für Angebote und Organisation",
            "für Büro und Baustelle",
        ],
    ),
]

SEARCH_INTENT_FALLBACKS = [
    "Ratgeber",
    "Praxisbuch",
    "Leitfaden",
    "Arbeitsbuch",
    "Journal",
    "Planer",
    "Tracker",
]


@dataclass(frozen=True)
class ExpansionResult:
    keyword: str
    keyword_type: str


def expand_keyword(seed: str) -> list[ExpansionResult]:
    normalized = " ".join((normalize_text(seed) or seed).strip().split())
    if not normalized:
        return []

    candidates: dict[str, ExpansionResult] = {}
    lowered = normalized.casefold()
    base_variants = _base_variants(normalized)
    modifiers = _modifier_pool(lowered)

    _add_candidate(candidates, normalized, "seed")
    for base_variant, keyword_type in base_variants:
        _add_candidate(candidates, base_variant, keyword_type)

    for base_variant, _ in base_variants[:8]:
        for modifier in modifiers:
            _add_candidate(candidates, f"{base_variant} {modifier}", "long_tail")

        for audience in GENERIC_AUDIENCES[:6]:
            for feature in _feature_pool(lowered)[:6]:
                _add_candidate(
                    candidates,
                    f"{base_variant} {audience} {feature}",
                    "audience_feature_long_tail",
                )

        for use_case in GENERIC_USE_CASES[:6]:
            for format_variant in GENERIC_FORMAT_VARIANTS[:4]:
                _add_candidate(
                    candidates,
                    f"{base_variant} {use_case} {format_variant}",
                    "use_case_variant",
                )

    for fallback in _search_intent_fallbacks(lowered):
        if fallback.casefold() not in lowered:
            _add_candidate(candidates, f"{normalized} {fallback}", "search_intent_variant")
            for audience in GENERIC_AUDIENCES[:4]:
                _add_candidate(
                    candidates,
                    f"{normalized} {fallback} {audience}",
                    "search_intent_long_tail",
                )

    expansions = sorted(candidates.values(), key=lambda item: item.keyword.casefold())
    return expansions[:MAX_EXPANSIONS]


def _base_variants(seed: str) -> list[tuple[str, str]]:
    lowered = seed.casefold()
    variants: list[tuple[str, str]] = [(seed, "seed_variant")]

    if " " not in seed:
        variants.extend((variant, "spacing_variant") for variant in _split_compound_keyword(seed))

    if "-" in seed:
        variants.append((" ".join(part for part in seed.split("-") if part), "hyphen_variant"))
    elif " " in seed:
        variants.append((seed.replace(" ", "-"), "hyphen_variant"))

    for token, config in INTENT_CONFIG.items():
        if token not in lowered:
            continue
        for replacement in config["replacements"]:
            swapped = _replace_case_insensitive(seed, token, replacement)
            variants.append((swapped, "semantic_variant"))
            for feature in config["features"]:
                variants.append((f"{swapped} {feature}", "intent_feature_variant"))

    deduped: list[tuple[str, str]] = []
    seen: set[str] = set()
    for variant, keyword_type in variants:
        normalized_variant = " ".join(variant.strip().split())
        key = normalized_variant.casefold()
        if not normalized_variant or key in seen:
            continue
        seen.add(key)
        deduped.append((normalized_variant, keyword_type))
    return deduped


def _modifier_pool(lowered_seed: str) -> list[str]:
    pool = [
        *GENERIC_AUDIENCES,
        *GENERIC_FEATURES,
        *GENERIC_USE_CASES,
        *GENERIC_FORMAT_VARIANTS,
        *_topic_specific_modifiers(lowered_seed),
    ]
    return _unique_strings(pool)


def _feature_pool(lowered_seed: str) -> list[str]:
    features = [*GENERIC_FEATURES, *_topic_specific_modifiers(lowered_seed)]
    for token, config in INTENT_CONFIG.items():
        if token in lowered_seed:
            features.extend(config["features"])
    return _unique_strings(features)


def _search_intent_fallbacks(lowered_seed: str) -> list[str]:
    fallbacks: list[str] = []
    for token, config in INTENT_CONFIG.items():
        if token in lowered_seed:
            fallbacks.extend(config["replacements"])
    fallbacks.extend(SEARCH_INTENT_FALLBACKS)
    return _unique_strings(fallbacks)


def _topic_specific_modifiers(lowered_seed: str) -> list[str]:
    modifiers: list[str] = []
    for tokens, tails in TOPIC_TAILS:
        if any(token in lowered_seed for token in tokens):
            modifiers.extend(tails)
    return modifiers


def _replace_case_insensitive(text: str, needle: str, replacement: str) -> str:
    lowered = text.casefold()
    index = lowered.find(needle.casefold())
    if index == -1:
        return text
    return text[:index] + replacement + text[index + len(needle) :]


def _split_compound_keyword(seed: str) -> list[str]:
    common_suffixes = [
        "tagebuch",
        "planer",
        "journal",
        "logbuch",
        "arbeitsbuch",
        "tracker",
        "ratgeber",
        "leitfaden",
        "handbuch",
    ]
    lowered = seed.casefold()
    variants: list[str] = []

    for suffix in common_suffixes:
        if lowered.endswith(suffix) and len(seed) > len(suffix):
            split_at = len(seed) - len(suffix)
            variants.append(f"{seed[:split_at]} {seed[split_at:]}")

    return variants


def _unique_strings(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(value.strip().split())
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return output


def _add_candidate(candidates: dict[str, ExpansionResult], keyword: str, keyword_type: str) -> None:
    normalized = " ".join(keyword.strip().split())
    if not normalized:
        return
    key = normalized.casefold()
    candidates.setdefault(key, ExpansionResult(keyword=normalized, keyword_type=keyword_type))
