from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.services.text_utils import normalize_text

if TYPE_CHECKING:
    from app.models.book import Book


NON_BOOK_TITLE_MARKERS = {
    "ampullen",
    "alltagsbegleiter",
    "booster",
    "brainwave monitoring",
    "bundle",
    "caps",
    "capsule",
    "capsules",
    "eiweiss",
    "flavor",
    "geschmack",
    "headband",
    "kapseln",
    "liquid",
    "marke:",
    "mehrkomponenten",
    "portionen",
    "post workout",
    "pre workout",
    "protein",
    "pulver",
    "real-time",
    "real time",
    "sensor",
    "shake",
    "shot",
    "store",
    "supplement",
    "wearable",
    "whey",
    "workout",
}
NON_BOOK_AUTHOR_MARKERS = {
    "besuche den",
    "marke:",
    "nutrition",
    "store",
}
BOOK_FORMAT_MARKERS = {
    "autor",
    "broschiert",
    "gebundene ausgabe",
    "hardcover",
    "kindle",
    "paperback",
    "taschenbuch",
}
NON_BOOK_MEASUREMENT_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:g|kg|mg|ml|l|oz|caps?|kapseln?|ampullen?|portionen?|sticks?|sachets?)\b"
)


def normalize_book_text(value: str | None) -> str:
    normalized = normalize_text(value) or ""
    return " ".join(normalized.casefold().split())


def has_non_book_markers(value: str | None) -> bool:
    normalized = normalize_book_text(value)
    if not normalized:
        return False
    if any(marker in normalized for marker in NON_BOOK_TITLE_MARKERS):
        return True
    return bool(NON_BOOK_MEASUREMENT_RE.search(normalized))


def is_probable_book_listing(
    title: str | None,
    *,
    author: str | None = None,
    formats: str | None = None,
) -> bool:
    normalized_title = normalize_book_text(title)
    if not normalized_title:
        return False
    if has_non_book_markers(normalized_title):
        return False

    normalized_author = normalize_book_text(author)
    if any(marker in normalized_author for marker in NON_BOOK_AUTHOR_MARKERS):
        return False

    normalized_formats = normalize_book_text(formats)
    if any(marker in normalized_formats for marker in BOOK_FORMAT_MARKERS):
        return True
    if any(marker in normalized_author for marker in BOOK_FORMAT_MARKERS):
        return True

    alpha_tokens = [
        token
        for token in re.split(r"[^0-9a-zA-Zäöüß]+", normalized_title)
        if token and any(char.isalpha() for char in token)
    ]
    if len(alpha_tokens) >= 2:
        return True
    return len(alpha_tokens) == 1 and len(alpha_tokens[0]) >= 6


def is_probable_book_record(book: Book) -> bool:
    if not is_probable_book_listing(book.title, author=book.author, formats=book.formats):
        return False
    if has_non_book_markers(book.author) or has_non_book_markers(book.publisher):
        return False

    has_strong_metadata = any(
        [
            normalize_book_text(book.author),
            normalize_book_text(book.formats),
            book.publication_date is not None,
            book.page_count is not None,
            normalize_book_text(book.primary_category),
            normalize_book_text(book.secondary_category),
            normalize_book_text(book.tertiary_category),
            normalize_book_text(book.table_of_contents),
        ]
    )
    if has_strong_metadata:
        return True

    raw_title = book.title or ""
    return any(separator in raw_title for separator in (":", " - ", " – ", " — "))
