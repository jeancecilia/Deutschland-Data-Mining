from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import mean

from app.models.book import Book
from app.models.review import ReviewCluster
from app.services.scoring_engine import clamp
from app.services.text_utils import normalize_text


AUDIENCE_PATTERNS = [
    ("senior", "Seniorinnen und Senioren"),
    ("anfänger", "Einsteigerinnen und Einsteiger"),
    ("selbstständ", "Selbstständige"),
    ("betrieb", "Kleine Betriebe"),
    ("eltern", "Eltern"),
    ("student", "Studierende"),
    ("handwerker", "Handwerkerinnen und Handwerker"),
    ("lehrer", "Lehrkräfte"),
]

REVIEW_AUDIENCE_PATTERNS = [
    ("arzt", "Menschen im medizinischen Dokumentationskontext"),
    ("patient", "Patientinnen und Patienten"),
    ("betrieb", "Betriebsinhaber und kleine Teams"),
    ("kunde", "Dienstleistungs- und Kundenkontakt-orientierte Leser"),
    ("praxis", "Praxisorientierte Anwender"),
]


@dataclass(frozen=True)
class CompetitorProfile:
    category_labels: list[str]
    listing_target_audience: str | None
    actual_target_audience: str | None
    listing_quality_score: int
    cover_quality_score: int
    freshness_score: int
    content_depth_score: int
    category_fit_score: int
    publication_age_years: float | None
    professional_publisher_signal: int
    series_signal: int
    table_of_contents_excerpt: str | None
    edition_info: str | None
    semantic_summary: str | None
    ai_target_audience: str | None
    ai_core_problem: str | None
    ai_use_case: str | None
    ai_promised_outcome: str | None
    ai_book_format: str | None
    ai_feature_terms: list[str]


def build_competitor_profile(
    keyword_text: str,
    book: Book,
    review_clusters: list[ReviewCluster],
) -> CompetitorProfile:
    ai_insight = book.ai_insight
    listing_target = ai_insight.target_audience if ai_insight and ai_insight.target_audience else infer_listing_target_audience(book)
    actual_target = infer_actual_target_audience(
        review_clusters,
        fallback=ai_insight.target_audience if ai_insight and ai_insight.target_audience else listing_target,
    )
    return CompetitorProfile(
        category_labels=category_labels_for_book(book),
        listing_target_audience=listing_target,
        actual_target_audience=actual_target,
        listing_quality_score=estimate_listing_quality_score(book),
        cover_quality_score=estimate_cover_quality_score(book),
        freshness_score=estimate_freshness_score(book),
        content_depth_score=estimate_content_depth_score(book, review_clusters),
        category_fit_score=estimate_category_fit_score(keyword_text, book),
        publication_age_years=estimate_publication_age_years(book),
        professional_publisher_signal=estimate_professional_publisher_signal(book),
        series_signal=estimate_series_signal(book),
        table_of_contents_excerpt=summarize_table_of_contents(book),
        edition_info=normalize_text(book.edition_info),
        semantic_summary=ai_insight.semantic_summary if ai_insight else None,
        ai_target_audience=ai_insight.target_audience if ai_insight else None,
        ai_core_problem=ai_insight.core_problem if ai_insight else None,
        ai_use_case=ai_insight.use_case if ai_insight else None,
        ai_promised_outcome=ai_insight.promised_outcome if ai_insight else None,
        ai_book_format=ai_insight.book_format if ai_insight else None,
        ai_feature_terms=ai_insight.feature_terms if ai_insight and ai_insight.feature_terms else [],
    )


def category_labels_for_book(book: Book) -> list[str]:
    labels = [
        normalize_text(book.primary_category),
        normalize_text(book.secondary_category),
        normalize_text(book.tertiary_category),
    ]
    output: list[str] = []
    seen: set[str] = set()
    for label in labels:
        if not label or label in seen:
            continue
        seen.add(label)
        output.append(label)
    return output


def infer_listing_target_audience(book: Book) -> str | None:
    text = " ".join(part for part in [book.title, book.subtitle, book.description] if part).casefold()
    for needle, audience in AUDIENCE_PATTERNS:
        if needle in text:
            return audience
    if "für " in text:
        fragment = text.split("für ", 1)[1].split(":", 1)[0].split("|", 1)[0].strip()
        if fragment:
            return fragment[:80].capitalize()
    return None


def infer_actual_target_audience(
    review_clusters: list[ReviewCluster],
    *,
    fallback: str | None = None,
) -> str | None:
    review_text = " ".join(
        part
        for cluster in review_clusters
        for part in [cluster.cluster_name, cluster.summary, cluster.example_snippets]
        if part
    ).casefold()
    for needle, audience in REVIEW_AUDIENCE_PATTERNS:
        if needle in review_text:
            return audience
    return fallback


def estimate_listing_quality_score(book: Book) -> int:
    description_length = len(book.description or "")
    subtitle_bonus = 12 if (book.subtitle or "").strip() else 0
    category_bonus = len(category_labels_for_book(book)) * 8
    page_bonus = min(16, (book.page_count or 0) // 20) if book.page_count else 0
    description_bonus = 28 if description_length >= 900 else 18 if description_length >= 450 else 8 if description_length >= 150 else 0
    format_bonus = 8 if (book.formats or "").strip() else 0
    toc_bonus = 12 if (book.table_of_contents or "").strip() else 0
    return clamp(20 + subtitle_bonus + category_bonus + page_bonus + description_bonus + format_bonus + toc_bonus)


def estimate_cover_quality_score(book: Book) -> int:
    title = normalize_text(book.title) or ""
    has_cover = 30 if book.cover_url else 0
    title_penalty = 10 if len(title) > 150 else 0
    subtitle_bonus = 12 if (book.subtitle or "").strip() else 0
    publisher_bonus = 6 if (book.publisher or "").strip() else 0
    category_bonus = 8 if category_labels_for_book(book) else 0
    return clamp(28 + has_cover + subtitle_bonus + publisher_bonus + category_bonus - title_penalty)


def estimate_freshness_score(book: Book) -> int:
    if book.publication_date is None:
        return 40
    age_years = max(0, date.today().year - book.publication_date.year)
    edition_boost = 10 if "auflage" in (book.edition_info or "").casefold() else 0
    return clamp(92 - age_years * 10 + edition_boost)


def estimate_publication_age_years(book: Book) -> float | None:
    if book.publication_date is None:
        return None
    days = max(0, (date.today() - book.publication_date).days)
    return round(days / 365.25, 2)


def estimate_content_depth_score(book: Book, review_clusters: list[ReviewCluster]) -> int:
    page_signal = min(28, (book.page_count or 0) // 8) if book.page_count else 8
    description_signal = 24 if len(book.description or "") >= 900 else 16 if len(book.description or "") >= 450 else 8
    toc_signal = 18 if (book.table_of_contents or "").strip() else 0
    negative_hits = sum(
        1
        for cluster in review_clusters
        if any(
            term in " ".join(
                part for part in [cluster.cluster_name, cluster.summary, cluster.example_snippets] if part
            ).casefold()
            for term in ["oberflächlich", "allgemein", "theoretisch", "struktur"]
        )
    )
    return clamp(20 + page_signal + description_signal + toc_signal - negative_hits * 8)


def estimate_category_fit_score(keyword_text: str, book: Book) -> int:
    keyword_tokens = {token for token in (normalize_text(keyword_text) or keyword_text).casefold().split() if len(token) > 3}
    book_tokens = {
        token
        for token in " ".join(category_labels_for_book(book) + [book.title or "", book.subtitle or ""]).casefold().split()
        if len(token) > 3
    }
    if not keyword_tokens or not book_tokens:
        return 35
    overlap = len(keyword_tokens & book_tokens)
    union = len(keyword_tokens | book_tokens)
    return clamp(25 + (overlap / max(1, union)) * 75)


def estimate_professional_publisher_signal(book: Book) -> int:
    publisher = (normalize_text(book.publisher) or "").casefold()
    if not publisher:
        return 18
    signal = 28
    if any(term in publisher for term in ["verlag", "publishing", "media", "press", "edition", "gmbh"]):
        signal += 36
    if len(publisher.split()) >= 2:
        signal += 12
    if any(char.isdigit() for char in publisher):
        signal -= 8
    return clamp(signal)


def estimate_series_signal(book: Book) -> int:
    text = " ".join(part for part in [book.title, book.subtitle, book.edition_info] if part).casefold()
    signal = 0
    for marker in ["band ", "teil ", "serie", "reihe", "vol.", "volume"]:
        if marker in text:
            signal += 35
    if ":" in (book.title or ""):
        signal += 10
    return clamp(signal)


def summarize_table_of_contents(book: Book) -> str | None:
    toc = normalize_text(book.table_of_contents)
    if toc:
        return toc[:260]
    description = normalize_text(book.description) or ""
    bullet_like = [part.strip() for part in description.split("•") if len(part.strip()) > 12]
    if bullet_like:
        return " | ".join(bullet_like[:4])[:260]
    return None


def average_profile_metric(profiles: list[CompetitorProfile], metric: str) -> int | None:
    values = [getattr(profile, metric) for profile in profiles if isinstance(getattr(profile, metric), int)]
    if not values:
        return None
    return clamp(mean(values))


def infer_cover_direction(keyword_text: str, book_class: str | None, audience: str | None) -> list[str]:
    audience_text = audience or "eine klar definierte deutsche Zielgruppe"
    lines = [
        "Klare Hauptbotschaft mit ruhiger, professioneller Typografie statt Keyword-Überladung.",
        f"Visuelle Sprache auf {audience_text} ausrichten, nicht auf generische Massenmarkt-Symbolik.",
    ]
    if book_class == "sachbuch":
        lines.append("Praxis- und Vertrauenssignal durch strukturierte Farbflächen, Icons und Deutschland-Bezug aufbauen.")
    else:
        lines.append("Nutzungskontext und Formatvorteil unmittelbar auf dem Cover lesbar machen.")
    return lines
