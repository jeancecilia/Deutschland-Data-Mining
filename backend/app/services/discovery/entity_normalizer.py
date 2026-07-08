"""
Entity Normalizer — normalizes German text for entity matching and deduplication.

Handles umlauts, ß, case folding, whitespace, and common German variations.
"""

from __future__ import annotations

import re
import unicodedata


# German-specific character mappings
_UMLAUT_MAP = str.maketrans({
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
    "ß": "ss",
})

_BOOK_FORMAT_TOKENS = {
    "tagebuch", "logbuch", "tracker", "planer", "journal",
    "arbeitsbuch", "workbook", "ratgeber", "leitfaden", "handbuch",
    "praxisbuch", "checklistenbuch", "vorlagenbuch", "ordner",
    "notizbuch", "trainingsbuch", "kochbuch", "lernplaner",
    "übungsbuch", "uebungsbuch", "sammlung",
}

_NOISE_WORDS = {
    "der", "die", "das", "ein", "eine", "einer", "eines",
    "und", "oder", "mit", "ohne", "von", "vom", "zum", "zur",
    "im", "in", "am", "an", "bei", "nach", "vor",
    "für", "fuer", "auf", "aus", "durch", "über", "ueber",
    "mein", "dein", "unser", "euer",
    "einfach", "schnell", "praktisch", "kompakt",
}


def normalize_german_text(text: str) -> str:
    """Normalize German text for comparison: lowercase, collapse whitespace, strip."""
    if not text:
        return ""
    normalized = text.casefold().strip()
    normalized = " ".join(normalized.split())
    return normalized


def _expand_umlauts(text: str) -> str:
    """Replace umlauts and ß with ASCII equivalents for fuzzy matching."""
    return text.translate(_UMLAUT_MAP)


def normalize_entity_name(name: str) -> str:
    """Normalize an entity name for deduplication.

    Steps:
      1. Lowercase + strip
      2. Remove trailing book-format tokens
      3. Remove leading noise words
      4. Normalize whitespace
      5. ASCII-fold for fuzzy matching
    """
    if not name:
        return ""

    text = normalize_german_text(name)

    # Remove trailing book-format tokens
    tokens = text.split()
    while tokens and tokens[-1] in _BOOK_FORMAT_TOKENS:
        tokens.pop()
    while tokens and tokens[0] in _NOISE_WORDS:
        tokens.pop(0)

    text = " ".join(tokens)

    # Expand umlauts for matching (fuzzy)
    text = _expand_umlauts(text)

    # Strip punctuation for matching
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = " ".join(text.split())

    return text[:255]


def are_names_equivalent(name_a: str, name_b: str) -> bool:
    """Check if two entity names refer to the same concept."""
    return normalize_entity_name(name_a) == normalize_entity_name(name_b)


def tokenize_for_matching(text: str) -> set[str]:
    """Return a set of normalized tokens useful for partial matching."""
    text = normalize_entity_name(text)
    return set(text.split()) - _NOISE_WORDS
