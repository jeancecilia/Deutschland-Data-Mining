"""Format-fit scoring rules — checks if a format makes sense for a given domain/topic."""

# Domain → suitable formats
DOMAIN_FORMAT_MAP: dict[str, list[str]] = {
    "pflege": ["checkliste", "ratgeber", "arbeitsbuch", "planer", "tagebuch"],
    "gesundheit": ["tagebuch", "tracker", "arbeitsbuch", "ratgeber", "logbuch"],
    "blutdruck": ["tagebuch", "tracker", "arbeitsbuch", "logbuch"],
    "diabetes": ["tagebuch", "tracker", "arbeitsbuch"],
    "business": ["arbeitsbuch", "vorlagenbuch", "checkliste", "ratgeber"],
    "buchhaltung": ["arbeitsbuch", "vorlagenbuch", "checkliste"],
    "haustiere": ["trainingsjournal", "ratgeber", "arbeitsbuch", "checkliste"],
    "hunde": ["trainingsjournal", "ratgeber", "arbeitsbuch"],
    "lernen": ["lernplaner", "arbeitsbuch", "karteikarten", "workbook"],
    "pruefung": ["lernplaner", "workbook", "arbeitsbuch", "checkliste"],
    "umzug": ["checkliste", "planer", "ratgeber"],
    "reise": ["planer", "checkliste", "tagebuch", "ratgeber"],
    "fitness": ["trainingsbuch", "planer", "tagebuch", "tracker"],
    "kochen": ["kochbuch", "planer", "tagebuch"],
    "garten": ["ratgeber", "planer", "tagebuch", "arbeitsbuch"],
    "finanzen": ["planer", "arbeitsbuch", "vorlagenbuch", "checkliste"],
    "haushalt": ["planer", "checkliste", "arbeitsbuch"],
    "senioren": ["ratgeber", "arbeitsbuch", "checkliste"],
    "smartphone": ["ratgeber", "arbeitsbuch"],
    "digital": ["ratgeber", "arbeitsbuch", "workbook"],
    "software": ["arbeitsbuch", "workbook", "leitfaden"],
    "marketing": ["arbeitsbuch", "planer", "leitfaden"],
}

# Format keywords → canonical format names
FORMAT_KEYWORDS: dict[str, str] = {
    "tagebuch": "tagebuch", "tagebücher": "tagebuch", "journal": "tagebuch",
    "tracker": "tracker", "tracking": "tracker", "logbuch": "tracker",
    "arbeitsbuch": "arbeitsbuch", "workbook": "arbeitsbuch",
    "checkliste": "checkliste", "checklist": "checkliste",
    "planer": "planer", "plan": "planer",
    "ratgeber": "ratgeber", "leitfaden": "ratgeber", "guide": "ratgeber",
    "trainingsjournal": "trainingsjournal", "trainingsbuch": "trainingsjournal",
    "vorlagenbuch": "vorlagenbuch", "vorlagen": "vorlagenbuch",
    "lernplaner": "lernplaner", "lernbuch": "lernplaner",
    "kochbuch": "kochbuch",
    "praxisbuch": "praxisbuch",
}


def detect_format(candidate_name: str) -> str | None:
    """Detect the format keyword from a candidate name."""
    lowered = candidate_name.lower()
    for keyword, canonical in FORMAT_KEYWORDS.items():
        if keyword in lowered:
            return canonical
    return None


def score_format_fit(
    candidate_name: str,
    macro_domain: str | None = None,
    subdomain: str | None = None,
) -> int:
    """Score 0–100 how well the format fits the domain."""
    fmt = detect_format(candidate_name)
    if not fmt:
        return 50  # neutral — no format detected

    # Check domain fit
    domain_key = (macro_domain or "").lower().replace("_", " ")
    subdomain_key = (subdomain or "").lower().replace("_", " ")

    for key in [subdomain_key, domain_key]:
        if key in DOMAIN_FORMAT_MAP:
            suitable = DOMAIN_FORMAT_MAP[key]
            if fmt in suitable:
                return 90  # strong match
            return 30  # mismatch
        # Try partial matching
        for dk, formats in DOMAIN_FORMAT_MAP.items():
            if dk in key or key in dk:
                if fmt in formats:
                    return 70  # partial match

    return 50  # unknown domain — neutral
