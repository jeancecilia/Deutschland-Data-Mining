from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from app.models.book import Book
from app.models.review import ReviewCluster
from app.services.text_utils import normalize_text


LOW_CONTENT_TERMS = {
    "tagebuch": 14,
    "logbuch": 14,
    "journal": 14,
    "tracker": 14,
    "planer": 14,
    "kalender": 12,
    "protokoll": 12,
    "pass": 10,
    "zum eintragen": 18,
    "messwerte": 10,
}

MEDIUM_CONTENT_TERMS = {
    "arbeitsbuch": 18,
    "checkliste": 10,
    "checklisten": 10,
    "vorlage": 10,
    "vorlagen": 10,
    "monatsübersicht": 12,
    "trendseiten": 12,
    "übungsbuch": 16,
    "praxisbuch": 12,
}

HIGH_CONTENT_TERMS = {
    "kompendium": 16,
    "handbuch": 14,
    "lehrbuch": 16,
    "kursbuch": 14,
    "prüfung": 12,
    "curriculum": 14,
    "zertifikat": 12,
}

SACHBUCH_TERMS = {
    "ratgeber": 16,
    "leitfaden": 18,
    "praxisratgeber": 20,
    "einfach erklärt": 10,
    "praxis": 10,
    "beispiele": 10,
    "strateg": 10,
    "grundlagen": 12,
    "kapitel": 10,
    "quellen": 10,
    "deutschland": 8,
    "selbstständ": 10,
    "betrieb": 10,
}


@dataclass(frozen=True)
class BookClassInference:
    book_class: str
    confidence: int
    evidence: list[str]
    low_content_signal: int
    medium_content_signal: int
    high_content_signal: int
    sachbuch_signal: int


def infer_book_class(
    keyword_text: str,
    books: list[Book],
    review_clusters: list[ReviewCluster],
    declared_book_type: str | None = None,
) -> BookClassInference:
    corpus_parts = [keyword_text]
    corpus_parts.extend(book.title or "" for book in books[:12])
    corpus_parts.extend(book.subtitle or "" for book in books[:12])
    corpus_parts.extend(book.description or "" for book in books[:12])
    corpus = " ".join(part for part in corpus_parts if part).casefold()

    page_counts = [book.page_count for book in books if book.page_count]
    avg_page_count = mean(page_counts) if page_counts else 0
    avg_description_length = mean([len(book.description or "") for book in books[:12]]) if books else 0
    subtitle_ratio = (
        sum(1 for book in books[:12] if (book.subtitle or "").strip()) / max(1, len(books[:12]))
        if books
        else 0.0
    )
    review_text = " ".join(
        part
        for cluster in review_clusters
        for part in [cluster.cluster_name, cluster.summary, cluster.example_snippets]
        if part
    ).casefold()

    low_signal = _score_terms(corpus, LOW_CONTENT_TERMS)
    medium_signal = _score_terms(corpus, MEDIUM_CONTENT_TERMS)
    high_signal = _score_terms(corpus, HIGH_CONTENT_TERMS)
    sachbuch_signal = _score_terms(corpus, SACHBUCH_TERMS)

    if avg_page_count and avg_page_count <= 120:
        low_signal += 12
    if 90 <= avg_page_count <= 180:
        medium_signal += 12
    if avg_page_count >= 170:
        high_signal += 10
        sachbuch_signal += 8

    if avg_description_length >= 500:
        sachbuch_signal += 18
    elif avg_description_length >= 250:
        medium_signal += 8
        sachbuch_signal += 8
    else:
        low_signal += 6

    if subtitle_ratio >= 0.55:
        sachbuch_signal += 10
        high_signal += 4
    elif subtitle_ratio <= 0.2:
        low_signal += 6

    if any(term in review_text for term in ["oberflächlich", "theoretisch", "beispiel", "praxis"]):
        sachbuch_signal += 10
    if any(term in review_text for term in ["eintragen", "formular", "layout"]):
        medium_signal += 6
        low_signal += 4

    declared = (declared_book_type or "").casefold()
    if declared == "sachbuch":
        sachbuch_signal += 8
    elif declared == "medium_content":
        medium_signal += 6
    elif declared == "low_content":
        low_signal += 6
    elif declared == "high_content":
        high_signal += 6

    signals = {
        "low_content": low_signal,
        "medium_content": medium_signal,
        "high_content": high_signal,
        "sachbuch": sachbuch_signal,
    }
    ordered = sorted(signals.items(), key=lambda item: item[1], reverse=True)
    top_class, top_score = ordered[0]
    second_score = ordered[1][1] if len(ordered) > 1 else 0
    confidence = max(35, min(99, 45 + (top_score - second_score)))

    evidence: list[str] = []
    if top_class == "sachbuch":
        evidence.append("Titel, Untertitel und Beschreibungen zeigen erklärende oder problemlösende Buchsignale.")
        if avg_description_length >= 500:
            evidence.append("Die Listings enthalten längere Beschreibungen statt bloßer Formular- oder Logbuchsprache.")
        if subtitle_ratio >= 0.55:
            evidence.append("Ein hoher Untertitel-Anteil deutet auf stärker positionierte Sachbuch-Listings hin.")
    elif top_class == "medium_content":
        evidence.append("Der Keywordraum zeigt strukturierte Nutzformate mit Templates, Checklisten oder Arbeitsbuch-Signalen.")
        if 90 <= avg_page_count <= 180:
            evidence.append("Der sichtbare Seitenumfang passt eher zu Medium-Content als zu einfachen Low-Content-Heften.")
    elif top_class == "high_content":
        evidence.append("Die Terminologie deutet auf umfangreichere Lehr-, Handbuch- oder Prüfungsformate hin.")
    else:
        evidence.append("Der Keywordraum wird von Logbuch-, Tagebuch- oder Eintragungsformaten dominiert.")
        if avg_page_count and avg_page_count <= 120:
            evidence.append("Der durchschnittliche Seitenumfang passt zu kompakten Eintrags- oder Tracking-Produkten.")

    return BookClassInference(
        book_class=top_class,
        confidence=confidence,
        evidence=evidence[:4],
        low_content_signal=low_signal,
        medium_content_signal=medium_signal,
        high_content_signal=high_signal,
        sachbuch_signal=sachbuch_signal,
    )


def _score_terms(corpus: str, weights: dict[str, int]) -> int:
    score = 0
    for term, weight in weights.items():
        if term in corpus:
            score += weight
    return min(100, score)
