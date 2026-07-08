from __future__ import annotations

import re


MOJIBAKE_MARKERS = ("Ã", "â", "€", "™", "œ", "ž", "Â")


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    text = re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()
    if not text:
        return text

    if any(marker in text for marker in MOJIBAKE_MARKERS):
        repaired = _repair_mojibake(text)
        if repaired is not None and _marker_count(repaired) < _marker_count(text):
            text = repaired

    return text


def _repair_mojibake(text: str) -> str | None:
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None


def _marker_count(text: str) -> int:
    return sum(text.count(marker) for marker in MOJIBAKE_MARKERS)
