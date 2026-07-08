from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from statistics import mean
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai import BookInsight
from app.models.book import Book
from app.models.review import Review
from app.schemas.analysis import NicheClusterAnalysisRead
from app.schemas.sachbuch import SachbuchAnalysisRead
from app.services.text_utils import normalize_text

try:
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - dependency is installed in Docker
    OpenAI = None


GERMAN_STOPWORDS = {
    "aber",
    "alle",
    "alltag",
    "auch",
    "bei",
    "bin",
    "buch",
    "das",
    "dass",
    "dem",
    "den",
    "der",
    "des",
    "die",
    "ein",
    "eine",
    "einem",
    "einen",
    "einer",
    "eines",
    "fuer",
    "für",
    "hat",
    "habe",
    "haben",
    "hier",
    "ich",
    "ihr",
    "ihre",
    "im",
    "ist",
    "kein",
    "keine",
    "kann",
    "mehr",
    "mein",
    "mit",
    "nach",
    "nicht",
    "noch",
    "oder",
    "schon",
    "sehr",
    "sich",
    "sind",
    "und",
    "von",
    "vor",
    "war",
    "wenn",
    "wie",
    "wird",
    "zum",
    "zur",
}

AUDIENCE_PATTERNS = {
    "senior": "Seniorinnen und Senioren",
    "angehör": "Angehoerige",
    "angehoer": "Angehoerige",
    "eltern": "Eltern",
    "student": "Studierende",
    "lehrer": "Lehrkraefte",
    "selbstständ": "Selbststaendige",
    "selbststaend": "Selbststaendige",
    "handwerker": "Handwerkerinnen und Handwerker",
    "hund": "Hundehalter",
    "adhs": "Erwachsene mit ADHS",
    "patient": "Patientinnen und Patienten",
}

FORMAT_PATTERNS = {
    "tagebuch": "Tagebuch",
    "planer": "Planer",
    "arbeitsbuch": "Arbeitsbuch",
    "checkliste": "Checklistenbuch",
    "checklistenbuch": "Checklistenbuch",
    "leitfaden": "Leitfaden",
    "tracker": "Tracker",
    "vorlage": "Vorlagenbuch",
    "ordner": "Ordner",
    "praxisbuch": "Praxisbuch",
    "workbook": "Workbook",
}

PROBLEM_PATTERNS = {
    "dokument": "Dokumentation und saubere Nachverfolgung",
    "struktur": "fehlende Struktur im Alltag",
    "routine": "Routinen aufbauen und halten",
    "überforder": "Ueberforderung reduzieren",
    "ueberforder": "Ueberforderung reduzieren",
    "zeit": "Zeitmangel und schnelle Orientierung",
    "antrag": "Antraege und formale Sicherheit",
    "symptom": "Symptome systematisch beobachten",
    "pflege": "Pflegeorganisation und Familienkoordination",
    "lernen": "Lernorganisation und Fokus halten",
}

REVIEW_THEME_RULES = {
    "space_for_writing": {
        "label": "zu wenig Platz zum Schreiben",
        "keywords": ["platz", "schreiben", "zeilen", "felder", "eintragen"],
        "improvement": "Mehr Schreibflaeche, klarere Eintragungsfelder und groessere Felder einplanen.",
    },
    "readability": {
        "label": "Schrift oder Layout schwer lesbar",
        "keywords": ["schrift", "lesbar", "lesen", "klein", "layout", "uebersichtlich", "übersichtlich"],
        "improvement": "Schriftgroesse, Weissraum und Seitenstruktur lesbarer machen.",
    },
    "depth_and_examples": {
        "label": "Inhalt zu oberflaechlich oder zu allgemein",
        "keywords": ["oberfl", "allgemein", "beispiel", "details", "tiefe", "praxis"],
        "improvement": "Mehr Beispiele, konkrete Anwendung und tiefere Erklaerungen ergaenzen.",
    },
    "templates_and_structure": {
        "label": "Struktur oder Vorlagen fehlen",
        "keywords": ["vorlage", "checkliste", "struktur", "ordnung", "tabelle", "formular"],
        "improvement": "Mehr direkt nutzbare Vorlagen, Checklisten und eine klarere Gliederung liefern.",
    },
    "localization": {
        "label": "Nicht gut an Deutschland angepasst",
        "keywords": ["deutschland", "deutsch", "übersetzung", "uebersetzung", "amerikanisch"],
        "improvement": "Terminologie, Beispiele und Hinweise staerker fuer Deutschland lokalisieren.",
    },
    "production_quality": {
        "label": "Machart oder Material enttaeuscht",
        "keywords": ["papier", "druck", "cover", "verarbeitung", "qualit"],
        "improvement": "Produktionsqualitaet, Druckbild und Coverversprechen besser abstimmen.",
    },
    "expectation_fit": {
        "label": "Nutzenversprechen wird nicht klar eingeloest",
        "keywords": ["erwart", "versprochen", "hilft", "unklar", "enttaeuscht"],
        "improvement": "Nutzenversprechen schaerfen und die Kernaufgabe klarer bedienen.",
    },
}

MISSING_MARKERS = ("fehlt", "fehlte", "wuensche", "wünsche", "mehr", "ohne", "vermisst")


class BookInsightPayload(BaseModel):
    semantic_summary: str | None = None
    target_audience: str | None = None
    core_problem: str | None = None
    use_case: str | None = None
    promised_outcome: str | None = None
    book_format: str | None = None
    feature_terms: list[str] = []
    category_terms: list[str] = []
    quality_flags: list[str] = []
    localization_notes: str | None = None
    confidence: int | None = None


class ReportSynthesisPayload(BaseModel):
    executive_summary: str
    gap_summary: str
    positioning_angles: list[str]
    metadata_strategy: list[str]
    title_ideas: list[str]
    subtitle_ideas: list[str]
    blueprint_summary: str
    risk_summary: str
    provider: str = "heuristic"
    model_name: str | None = None
    confidence: int = 50


@dataclass
class ReviewSignal:
    review: Review
    sentiment: str
    cluster_type: str
    theme_key: str
    semantic_label: str
    summary_text: str
    suggested_improvement: str | None
    audience_hint: str | None
    missing_feature: str | None
    buyer_words: list[str]
    evidence_terms: list[str]
    confidence: int


@lru_cache
def _get_client() -> OpenAI | None:
    settings = get_settings()
    if not settings.ai_runtime_enabled or OpenAI is None:
        return None

    kwargs: dict[str, object] = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)


def upsert_book_insight(db: Session, book: Book, *, commit: bool = True) -> BookInsight | None:
    text_parts = [
        book.title,
        book.subtitle,
        book.description,
        book.primary_category,
        book.secondary_category,
        book.tertiary_category,
        book.table_of_contents,
    ]
    if not any(part and part.strip() for part in text_parts):
        return None

    ai_payload = _extract_book_insight_via_ai(book)
    provider = "openai" if ai_payload is not None else "heuristic"
    payload = ai_payload or _extract_book_insight_heuristic(book)
    semantic_key = _compose_semantic_key(
        [
            payload.target_audience,
            payload.core_problem,
            payload.use_case,
            payload.book_format,
            *(payload.feature_terms[:3] if payload.feature_terms else []),
        ]
    )

    insight = db.scalars(select(BookInsight).where(BookInsight.book_id == book.id)).first()
    if insight is None:
        insight = BookInsight(book_id=book.id)

    settings = get_settings()
    insight.provider = provider
    insight.model_name = settings.ai_model if provider == "openai" else "heuristic-v1"
    insight.semantic_key = semantic_key
    insight.semantic_summary = payload.semantic_summary
    insight.target_audience = _truncate_text(payload.target_audience, limit=255)
    insight.core_problem = _truncate_text(payload.core_problem, limit=255)
    insight.use_case = _truncate_text(payload.use_case, limit=255)
    insight.promised_outcome = _truncate_text(payload.promised_outcome, limit=255)
    insight.book_format = _truncate_text(payload.book_format, limit=100)
    insight.feature_terms = _dedupe_strings(payload.feature_terms)[:10]
    insight.category_terms = _dedupe_strings(payload.category_terms)[:8]
    insight.quality_flags = _dedupe_strings(payload.quality_flags)[:8]
    insight.localization_notes = payload.localization_notes
    insight.confidence = _clamp_int(payload.confidence or 55)
    insight.raw_payload = payload.model_dump()
    db.add(insight)
    if commit:
        db.commit()
        db.refresh(insight)
    return insight


def semantic_key_for_candidate_phrase(phrase: str) -> tuple[str | None, str | None]:
    normalized = normalize_text(phrase) or phrase
    tokens = _semantic_tokens(normalized)
    if not tokens:
        return None, None
    semantic_key = " | ".join(tokens[:5])[:255]
    semantic_family = " ".join(tokens[:3])[:255]
    return semantic_key, semantic_family


def semantic_text_similarity(left: str, right: str) -> float:
    left_vector = _local_embedding(left)
    right_vector = _local_embedding(right)
    return _cosine_similarity(left_vector, right_vector)


def cluster_reviews_semantically(
    reviews: list[Review],
) -> tuple[list[dict[str, object]], str]:
    signals = [_build_review_signal(review) for review in reviews if (review.title or review.body)]
    if not signals:
        return [], "heuristic"

    vectors, source = _vectorize_texts([signal.summary_text for signal in signals], prefer_remote=True)
    threshold = get_settings().ai_semantic_similarity_threshold
    buckets: list[dict[str, object]] = []

    for index, signal in enumerate(signals):
        assigned = False
        for bucket in buckets:
            if signal.sentiment != bucket["sentiment"]:
                continue
            similarity = _cosine_similarity(vectors[index], bucket["centroid"])
            required_similarity = threshold if signal.theme_key == bucket["theme_key"] else threshold + 0.05
            if similarity < required_similarity:
                continue
            bucket["signals"].append(signal)
            bucket["vectors"].append(vectors[index])
            bucket["centroid"] = _average_vectors(bucket["vectors"])
            assigned = True
            break

        if assigned:
            continue

        buckets.append(
            {
                "signals": [signal],
                "vectors": [vectors[index]],
                "centroid": vectors[index],
                "sentiment": signal.sentiment,
                "theme_key": signal.theme_key,
            }
        )

    clusters = [_summarize_review_bucket(bucket, source_method=source) for bucket in buckets]
    clusters.sort(key=lambda item: (-(item["frequency"] or 0), -(item["confidence_score"] or 0)))
    return clusters, source


def build_report_synthesis(
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
) -> ReportSynthesisPayload:
    fallback = _build_report_synthesis_fallback(cluster_analysis, sachbuch_analysis)
    client = _get_client()
    if client is None:
        return fallback

    payload = {
        "main_keyword": cluster_analysis.main_keyword,
        "recommended_book_class": cluster_analysis.recommended_book_class,
        "score": cluster_analysis.score.model_dump(),
        "top_complaints": cluster_analysis.top_complaints[:5],
        "top_opportunities": cluster_analysis.top_opportunities[:5],
        "missing_features": cluster_analysis.missing_features[:5],
        "audience_hints": cluster_analysis.audience_hints[:5],
        "positive_review_signals": cluster_analysis.positive_review_signals[:5],
        "keyword_strategy": cluster_analysis.keyword_strategy.model_dump(),
        "category_strategy": cluster_analysis.category_strategy.model_dump(),
        "competitor_summary": cluster_analysis.competitor_summary.model_dump(),
        "competitors": [
            {
                "title": book.title,
                "audience": book.ai_target_audience or book.actual_target_audience or book.listing_target_audience,
                "problem": book.ai_core_problem,
                "use_case": book.ai_use_case,
                "format": book.ai_book_format or book.formats,
                "strengths": book.strengths[:3],
                "weaknesses": book.weaknesses[:3],
                "review_count": book.latest_review_count,
                "bsr": book.bsr.latest_bsr,
            }
            for book in cluster_analysis.competitor_books[:8]
        ],
        "sachbuch": sachbuch_analysis.model_dump() if sachbuch_analysis else None,
    }

    prompt = (
        "You are generating structured KDP opportunity synthesis for Germany. "
        "Use only the supplied evidence. Do not invent demand, reviews, or competitive facts. "
        "Return valid JSON only with these keys: executive_summary, gap_summary, positioning_angles, "
        "metadata_strategy, title_ideas, subtitle_ideas, blueprint_summary, risk_summary, confidence. "
        "executive_summary, gap_summary, blueprint_summary, and risk_summary must be plain strings. "
        "positioning_angles, metadata_strategy, title_ideas, and subtitle_ideas must be arrays of plain strings. "
        "Do not return nested objects. Keep every field concise: summaries under 90 words, "
        "lists capped at 5 items, and each list item under 18 words."
    )
    response = _call_json_response(prompt, payload, max_output_tokens=2600)
    if response is None:
        return fallback

    try:
        synthesis = ReportSynthesisPayload.model_validate(
            {
                **_normalize_report_synthesis_response(response),
                "provider": "openai",
                "model_name": get_settings().ai_model,
            }
        )
    except ValidationError:
        return fallback

    return synthesis


def _extract_book_insight_via_ai(book: Book) -> BookInsightPayload | None:
    client = _get_client()
    if client is None:
        return None

    payload = {
        "title": book.title,
        "subtitle": book.subtitle,
        "description": _truncate(book.description),
        "categories": [book.primary_category, book.secondary_category, book.tertiary_category],
        "table_of_contents": _truncate(book.table_of_contents, limit=1800),
        "formats": book.formats,
        "page_count": book.page_count,
    }
    prompt = (
        "Extract structured KDP listing intelligence for the German market. "
        "Use only explicit evidence from the provided listing text. "
        "Return valid JSON only with keys: semantic_summary, target_audience, core_problem, use_case, "
        "promised_outcome, book_format, feature_terms, category_terms, quality_flags, localization_notes, confidence."
    )
    response = _call_json_response(prompt, payload)
    if response is None:
        return None

    try:
        return BookInsightPayload.model_validate(_normalize_book_insight_response(response))
    except ValidationError:
        return None


def _extract_book_insight_heuristic(book: Book) -> BookInsightPayload:
    listing_text = " ".join(
        part for part in [book.title, book.subtitle, book.description, book.table_of_contents] if part
    )
    normalized = (normalize_text(listing_text) or listing_text).casefold()
    categories = [
        value
        for value in [
            normalize_text(book.primary_category),
            normalize_text(book.secondary_category),
            normalize_text(book.tertiary_category),
        ]
        if value
    ]
    audience = _infer_from_patterns(normalized, AUDIENCE_PATTERNS)
    book_format = _infer_from_patterns(normalized, FORMAT_PATTERNS)
    core_problem = _infer_from_patterns(normalized, PROBLEM_PATTERNS)
    use_case = _infer_use_case(normalized)
    feature_terms = _top_terms(
        " ".join(
            part for part in [book.title, book.subtitle, book.description, book.table_of_contents] if part
        ),
        limit=8,
    )
    promised_outcome = _infer_promised_outcome(book.title, book.subtitle, book.description)
    quality_flags: list[str] = []
    if len(book.description or "") < 220:
        quality_flags.append("Short listing description")
    if not (book.table_of_contents or "").strip() and (book.page_count or 0) >= 120:
        quality_flags.append("No visible structure cues")
    if not categories:
        quality_flags.append("Category signal incomplete")

    localization_notes = None
    if any(term in normalized for term in ["deutschland", "deutsch", "pflegegrad", "behörde", "behoerde"]):
        localization_notes = "Visible Germany-specific terminology or process framing."

    summary_parts = [audience, core_problem, use_case, book_format]
    semantic_summary = ", ".join(part for part in summary_parts if part)
    if not semantic_summary:
        semantic_summary = f"{book.title or book.asin}: practice-oriented German KDP listing."

    return BookInsightPayload(
        semantic_summary=semantic_summary,
        target_audience=audience,
        core_problem=core_problem,
        use_case=use_case,
        promised_outcome=promised_outcome,
        book_format=book_format or normalize_text(book.formats),
        feature_terms=feature_terms,
        category_terms=categories[:8],
        quality_flags=quality_flags,
        localization_notes=localization_notes,
        confidence=62,
    )


def _normalize_book_insight_response(response: dict[str, object]) -> dict[str, object]:
    normalized = dict(response)
    normalized["semantic_summary"] = _coerce_to_text(response.get("semantic_summary"))
    normalized["target_audience"] = _coerce_primary_text(response.get("target_audience"))
    normalized["core_problem"] = _coerce_to_text(response.get("core_problem"))
    normalized["use_case"] = _coerce_to_text(response.get("use_case"))
    normalized["promised_outcome"] = _coerce_to_text(response.get("promised_outcome"))
    normalized["book_format"] = _coerce_book_format_text(response.get("book_format"))
    normalized["feature_terms"] = _coerce_string_list(response.get("feature_terms"))
    normalized["category_terms"] = _coerce_string_list(response.get("category_terms"))
    normalized["quality_flags"] = _coerce_string_list(response.get("quality_flags"))
    normalized["localization_notes"] = _coerce_to_text(response.get("localization_notes"))
    normalized["confidence"] = _coerce_confidence_score(response.get("confidence"))
    return normalized


def _normalize_report_synthesis_response(response: dict[str, object]) -> dict[str, object]:
    normalized = dict(response)
    normalized["executive_summary"] = _coerce_report_summary_text(response.get("executive_summary"))
    normalized["gap_summary"] = _coerce_report_gap_text(response.get("gap_summary"))
    normalized["positioning_angles"] = _coerce_report_string_list(
        response.get("positioning_angles"),
        preferred_keys=("angle", "positioning_note"),
    )
    normalized["metadata_strategy"] = _coerce_report_string_list(
        response.get("metadata_strategy"),
        preferred_keys=("primary_keywords", "secondary_keywords", "backend_keywords", "category_notes"),
    )
    normalized["title_ideas"] = _coerce_report_string_list(response.get("title_ideas"))
    normalized["subtitle_ideas"] = _coerce_report_string_list(response.get("subtitle_ideas"))
    normalized["blueprint_summary"] = _coerce_report_summary_text(response.get("blueprint_summary"))
    normalized["risk_summary"] = _coerce_report_summary_text(response.get("risk_summary"))
    normalized["confidence"] = _coerce_confidence_score(response.get("confidence"))
    return normalized


def _build_review_signal(review: Review) -> ReviewSignal:
    text = " ".join(part for part in [review.title, review.body] if part)
    normalized = (normalize_text(text) or text).casefold()
    sentiment = _review_sentiment(review.rating)
    best_theme = "general_feedback"
    best_matches = 0

    for theme_key, config in REVIEW_THEME_RULES.items():
        matches = sum(1 for keyword in config["keywords"] if keyword in normalized)
        if matches > best_matches:
            best_theme = theme_key
            best_matches = matches

    rule = REVIEW_THEME_RULES.get(best_theme, {})
    label = str(rule.get("label", "wiederkehrendes Review-Signal"))
    cluster_type = "praise" if sentiment == "positive" else "complaint"
    if any(marker in normalized for marker in MISSING_MARKERS):
        cluster_type = "missing_feature"

    audience_hint = _infer_from_patterns(normalized, AUDIENCE_PATTERNS)
    buyer_words = _top_terms(text, limit=5)
    missing_feature = None
    if cluster_type == "missing_feature":
        missing_feature = " ".join(buyer_words[:3]) if buyer_words else label
    evidence_terms = [keyword for keyword in rule.get("keywords", []) if keyword in normalized][:5]
    summary_text = label
    if buyer_words:
        summary_text += f" | {', '.join(buyer_words[:3])}"

    confidence = 52 + best_matches * 10
    if review.rating is not None:
        confidence += 8

    return ReviewSignal(
        review=review,
        sentiment=sentiment,
        cluster_type=cluster_type,
        theme_key=best_theme,
        semantic_label=label,
        summary_text=summary_text,
        suggested_improvement=str(rule.get("improvement")) if rule else None,
        audience_hint=audience_hint,
        missing_feature=missing_feature,
        buyer_words=buyer_words,
        evidence_terms=evidence_terms,
        confidence=_clamp_int(confidence),
    )


def _summarize_review_bucket(bucket: dict[str, object], *, source_method: str) -> dict[str, object]:
    signals = bucket["signals"]
    assert isinstance(signals, list)
    typed_signals = [signal for signal in signals if isinstance(signal, ReviewSignal)]
    counts = Counter(signal.semantic_label for signal in typed_signals)
    label = counts.most_common(1)[0][0]
    theme_key = Counter(signal.theme_key for signal in typed_signals).most_common(1)[0][0]
    cluster_type = Counter(signal.cluster_type for signal in typed_signals).most_common(1)[0][0]
    sentiment = str(bucket["sentiment"])
    snippets = [
        _compact_snippet(" ".join(part for part in [signal.review.title, signal.review.body] if part))
        for signal in typed_signals
    ]
    buyer_words = _dedupe_strings([word for signal in typed_signals for word in signal.buyer_words])[:8]
    evidence_terms = _dedupe_strings([word for signal in typed_signals for word in signal.evidence_terms])[:8]
    missing_features = [signal.missing_feature for signal in typed_signals if signal.missing_feature]
    audience_hints = [signal.audience_hint for signal in typed_signals if signal.audience_hint]
    improvements = [signal.suggested_improvement for signal in typed_signals if signal.suggested_improvement]
    frequency = len(typed_signals)
    semantic_key = _compose_semantic_key([theme_key, label, *buyer_words[:3], *missing_features[:1]])

    if sentiment == "negative":
        severity = min(5, max((5 - (signal.review.rating or 3)) for signal in typed_signals))
    elif sentiment == "mixed":
        severity = 3
    else:
        severity = 1

    if sentiment == "positive":
        summary = f"{frequency} review(s) explicitly praise: {label}."
    elif cluster_type == "missing_feature":
        summary = f"{frequency} review(s) repeatedly point to a missing element around: {label}."
    else:
        summary = f"{frequency} review(s) criticize or question: {label}."

    return {
        "cluster_name": label,
        "sentiment": sentiment,
        "frequency": frequency,
        "severity": severity,
        "summary": summary,
        "example_snippets": " | ".join(snippet for snippet in snippets if snippet)[:1000] or None,
        "suggested_improvements": improvements[0] if improvements else None,
        "cluster_type": cluster_type,
        "theme_key": theme_key,
        "semantic_key": semantic_key,
        "source_method": source_method,
        "confidence_score": _clamp_int(mean(signal.confidence for signal in typed_signals)),
        "buyer_words": buyer_words or None,
        "audience_hint": audience_hints[0] if audience_hints else None,
        "missing_feature": missing_features[0] if missing_features else None,
        "evidence_terms": evidence_terms or None,
    }


def _build_report_synthesis_fallback(
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
) -> ReportSynthesisPayload:
    audience = ", ".join(cluster_analysis.audience_hints[:2]) or "klar definierte deutschsprachige Kaeufer"
    score = cluster_analysis.score.final_score or 0
    executive_summary = (
        f"{cluster_analysis.main_keyword} zeigt mit Score {score}/100 eine "
        f"{'starke' if score >= 65 else 'mittlere' if score >= 40 else 'schwache'} Chance. "
        f"Die sichtbarste Zielgruppe ist {audience}."
    )
    gap_summary = " ".join((cluster_analysis.top_opportunities[:2] + cluster_analysis.missing_features[:2])[:4])
    if not gap_summary:
        gap_summary = "Noch keine klaren Luecken aus Wettbewerber- und Reviewdaten gespeichert."
    positioning_angles = _dedupe_strings(
        [
            *(cluster_analysis.top_opportunities[:3]),
            f"Explizit fuer {audience} positionieren.",
            "Deutschland-Bezug und klare Alltagssituation sichtbarer machen."
            if any("deutsch" in (hint or "").casefold() for hint in cluster_analysis.audience_hints)
            else None,
        ]
    )[:4]
    metadata_strategy = _dedupe_strings(
        [
            f"Hauptkeyword '{cluster_analysis.main_keyword}' frueh im Titel platzieren.",
            *(cluster_analysis.keyword_strategy.primary_keywords[:3]),
            *(cluster_analysis.category_strategy.visibility_opportunities[:2]),
        ]
    )[:5]
    base_title = cluster_analysis.main_keyword
    title_ideas = _dedupe_strings(
        [
            f"{base_title} fuer {cluster_analysis.audience_hints[0]}" if cluster_analysis.audience_hints else base_title,
            f"{base_title} Praxisbuch" if cluster_analysis.recommended_book_class == "sachbuch" else f"{base_title} Planer",
            f"{base_title} im Alltag",
        ]
    )[:3]
    subtitle_ideas = _dedupe_strings(
        [
            gap_summary,
            "Mit klarer Struktur, praktischen Vorlagen und deutscher Terminologie.",
            "Fokus auf Alltag, schnelle Umsetzung und weniger Reibung.",
        ]
    )[:3]
    blueprint_summary = (
        "Kapitelweise von Problemklaerung zu praktischer Umsetzung und wiederkehrenden Arbeitshilfen fuehren."
        if sachbuch_analysis
        else "Mit schneller Einstiegserklaerung, klaren Seitenmustern und direkt nutzbaren Templates starten."
    )
    risk_summary = (
        f"Authority Risk {cluster_analysis.score.authority_risk}, Compliance Risk {cluster_analysis.score.compliance_risk}, "
        f"Review Wall {cluster_analysis.score.review_wall_risk}."
    )
    return ReportSynthesisPayload(
        executive_summary=executive_summary,
        gap_summary=gap_summary,
        positioning_angles=positioning_angles,
        metadata_strategy=metadata_strategy,
        title_ideas=title_ideas,
        subtitle_ideas=subtitle_ideas,
        blueprint_summary=blueprint_summary,
        risk_summary=risk_summary,
        provider="heuristic",
        model_name="heuristic-v1",
        confidence=58,
    )


def _call_json_response(
    prompt: str,
    payload: dict[str, object],
    *,
    max_output_tokens: int = 1400,
) -> dict[str, object] | None:
    client = _get_client()
    if client is None:
        return None

    settings = get_settings()
    try:
        response = client.responses.create(
            model=settings.ai_model,
            input=[
                {"role": "developer", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False, default=str)[: settings.ai_max_text_chars],
                },
            ],
            max_output_tokens=max_output_tokens,
        )
    except Exception:
        return None

    raw_text = getattr(response, "output_text", None)
    if not raw_text:
        return None

    parsed = _extract_json_object(raw_text)
    if not isinstance(parsed, dict):
        return None
    return parsed


def _vectorize_texts(texts: list[str], *, prefer_remote: bool) -> tuple[list[list[float]], str]:
    if prefer_remote:
        remote_vectors = _embed_texts_remote(texts)
        if remote_vectors is not None:
            return remote_vectors, "openai_embeddings"
    return [_local_embedding(text) for text in texts], "heuristic"


def _embed_texts_remote(texts: list[str]) -> list[list[float]] | None:
    client = _get_client()
    if client is None or not texts:
        return None

    settings = get_settings()
    kwargs: dict[str, object] = {
        "model": settings.ai_embedding_model,
        "input": [text[:1500] for text in texts],
    }
    if settings.ai_embedding_dimensions is not None:
        kwargs["dimensions"] = settings.ai_embedding_dimensions

    try:
        response = client.embeddings.create(**kwargs)
    except Exception:
        return None

    vectors: list[list[float]] = []
    for item in response.data:
        embedding = getattr(item, "embedding", None)
        if not isinstance(embedding, list):
            return None
        vectors.append(_normalize_vector([float(value) for value in embedding]))
    return vectors if len(vectors) == len(texts) else None


def _extract_json_object(raw_text: str) -> Any:
    text = raw_text.strip()
    if text.startswith("```"):
        fenced = text.split("```")
        if len(fenced) >= 3:
            text = fenced[1]
            if "\n" in text:
                text = text.split("\n", 1)[1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def _coerce_to_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, list):
        parts = [_coerce_to_text(item) for item in value]
        joined = "; ".join(part for part in parts if part)
        return joined[:1000] or None
    if isinstance(value, dict):
        parts = [f"{key}: {_coerce_to_text(item)}" for key, item in value.items() if _coerce_to_text(item)]
        joined = "; ".join(parts)
        return joined[:1000] or None
    text = str(value).strip()
    return text or None


def _coerce_primary_text(value: object) -> str | None:
    if isinstance(value, list):
        for item in value:
            text = _coerce_to_text(item)
            if text:
                return text[:255]
        return None
    text = _coerce_to_text(value)
    return text[:255] if text else None


def _coerce_book_format_text(value: object) -> str | None:
    if isinstance(value, dict):
        for key in ("type", "format", "name"):
            text = _coerce_to_text(value.get(key))
            if text:
                return text[:100]
        return _coerce_to_text(value)
    text = _coerce_to_text(value)
    return text[:100] if text else None


def _coerce_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = [_coerce_to_text(item) for item in value]
        return _dedupe_strings([item for item in items if item])[:24]
    text = _coerce_to_text(value)
    return [text] if text else []


def _coerce_confidence_score(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 100 if value else 0
    if isinstance(value, (int, float)):
        numeric = float(value)
        if 0 <= numeric <= 1:
            numeric *= 100
        return _clamp_int(round(numeric))
    text = _coerce_to_text(value)
    if not text:
        return None
    try:
        numeric = float(text)
    except ValueError:
        match = re.search(r"(\d{1,3})(?:\s*/\s*100)?", text)
        if match:
            return _clamp_int(int(match.group(1)))
        lowered = text.casefold()
        if "high" in lowered or "stark" in lowered or "hoch" in lowered:
            return 85
        if "medium" in lowered or "moderat" in lowered or "mittel" in lowered:
            return 65
        if "low" in lowered or "niedrig" in lowered or "schwach" in lowered:
            return 40
        return None
    if 0 <= numeric <= 1:
        numeric *= 100
    return _clamp_int(round(numeric))


def _coerce_report_summary_text(value: object) -> str | None:
    if isinstance(value, dict):
        preferred_parts = [
            _coerce_to_text(value.get("summary")),
            _coerce_to_text(value.get("opportunity_assessment")),
            _coerce_to_text(value.get("market_read")),
            _coerce_to_text(value.get("caution")),
            _coerce_to_text(value.get("recommendation")),
        ]
        evidence = _coerce_report_string_list(
            value.get("key_evidence"),
            preferred_keys=("summary", "label", "angle"),
        )
        parts = [part for part in preferred_parts if part]
        if evidence:
            parts.append("Evidence: " + "; ".join(evidence[:4]))
        text = " ".join(parts)
        return text[:1400] or None
    return _coerce_to_text(value)


def _coerce_report_gap_text(value: object) -> str | None:
    if isinstance(value, dict):
        gaps = _coerce_report_string_list(
            value.get("confirmed_gaps"),
            preferred_keys=("summary", "label"),
        )
        caution = _coerce_to_text(value.get("caution"))
        signals = _coerce_report_string_list(
            value.get("usable_review_signals"),
            preferred_keys=("summary", "label"),
        )
        parts: list[str] = []
        if gaps:
            parts.append("Confirmed gaps: " + "; ".join(gaps[:4]))
        if caution:
            parts.append("Caution: " + caution)
        if signals:
            parts.append("Signals: " + "; ".join(signals[:3]))
        text = " ".join(parts)
        return text[:1400] or None
    return _coerce_to_text(value)


def _coerce_report_string_list(
    value: object,
    *,
    preferred_keys: tuple[str, ...] = ("title", "label", "summary", "name"),
) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        output: list[str] = []
        for item in value:
            if isinstance(item, dict):
                for key in preferred_keys:
                    text = _coerce_to_text(item.get(key))
                    if text:
                        output.append(text[:280])
                        break
                else:
                    text = _coerce_to_text(item)
                    if text:
                        output.append(text[:280])
                continue
            text = _coerce_to_text(item)
            if text:
                output.append(text[:280])
        return _dedupe_strings(output)[:12]
    if isinstance(value, dict):
        output: list[str] = []
        for key in preferred_keys:
            items = _coerce_string_list(value.get(key))
            output.extend(item[:280] for item in items)
        if not output:
            text = _coerce_to_text(value)
            if text:
                output.append(text[:280])
        return _dedupe_strings(output)[:12]
    text = _coerce_to_text(value)
    return [text[:280]] if text else []


def _local_embedding(text: str, *, dimensions: int = 96) -> list[float]:
    vector = [0.0] * dimensions
    for token in _semantic_tokens(text):
        digest = sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        weight = 1.0 + min(len(token), 14) / 14
        vector[index] += sign * weight
    return _normalize_vector(vector)


def _normalize_vector(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def _average_vectors(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    width = len(vectors[0])
    totals = [0.0] * width
    for vector in vectors:
        for index, value in enumerate(vector):
            totals[index] += value
    return _normalize_vector([value / len(vectors) for value in totals])


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=False))


def _semantic_tokens(text: str) -> list[str]:
    normalized = (normalize_text(text) or text).casefold()
    cleaned = (
        normalized.replace("/", " ")
        .replace("-", " ")
        .replace(":", " ")
        .replace(",", " ")
        .replace(".", " ")
    )
    tokens = [token.strip() for token in cleaned.split()]
    return [
        token
        for token in tokens
        if len(token) >= 4 and token not in GERMAN_STOPWORDS and any(char.isalpha() for char in token)
    ]


def _top_terms(text: str | None, *, limit: int) -> list[str]:
    if not text:
        return []
    counts: Counter[str] = Counter(_semantic_tokens(text))
    return [token for token, _ in counts.most_common(limit)]


def _infer_from_patterns(text: str, mapping: dict[str, str]) -> str | None:
    for needle, value in mapping.items():
        if needle in text:
            return value
    return None


def _infer_use_case(text: str) -> str | None:
    for marker, label in [
        ("alltag", "im Alltag mit schneller Nutzung"),
        ("krankenhaus", "nach einem sensiblen Uebergang oder Gesundheitsereignis"),
        ("famil", "im Familienalltag mit mehreren Rollen"),
        ("beruf", "im Berufsalltag mit Zeitdruck"),
        ("behörd", "bei Formularen, Fristen und Behoerdenkontakt"),
        ("behoerd", "bei Formularen, Fristen und Behoerdenkontakt"),
        ("zuhause", "fuer Zuhause ohne professionelle Begleitung"),
    ]:
        if marker in text:
            return label
    return None


def _infer_promised_outcome(title: str | None, subtitle: str | None, description: str | None) -> str | None:
    haystack = " ".join(part for part in [title, subtitle, description] if part)
    normalized = (normalize_text(haystack) or haystack).casefold()
    for keyword, promise in [
        ("organis", "mehr Ordnung und bessere Uebersicht"),
        ("dokument", "saubere Nachverfolgung und weniger Fehler"),
        ("routine", "bessere Gewohnheiten und Kontinuitaet"),
        ("check", "schnellere Umsetzung mit klaren Schritten"),
        ("hilfe", "spuerbare Entlastung und Orientierung"),
    ]:
        if keyword in normalized:
            return promise
    return None


def _compose_semantic_key(parts: list[str | None]) -> str | None:
    tokens = _semantic_tokens(" ".join(part for part in parts if part))
    if not tokens:
        return None
    return " | ".join(tokens[:5])[:255]


def _review_sentiment(rating: int | None) -> str:
    if rating is None:
        return "mixed"
    if rating >= 4:
        return "positive"
    if rating <= 2:
        return "negative"
    return "mixed"


def _compact_snippet(text: str | None) -> str | None:
    normalized = normalize_text(text)
    if not normalized:
        return None
    return normalized[:180]


def _truncate(value: str | None, *, limit: int = 2200) -> str | None:
    normalized = normalize_text(value)
    if normalized is None:
        return None
    return normalized[:limit]


def _truncate_text(value: str | None, *, limit: int) -> str | None:
    normalized = normalize_text(value)
    if not normalized:
        return None
    return normalized[:limit]


def _dedupe_strings(values: list[str | None]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_text(value)
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return output


def _clamp_int(value: float | int, *, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, int(round(value))))
