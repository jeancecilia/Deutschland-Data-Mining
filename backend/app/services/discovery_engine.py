from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re
from statistics import median

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.discovery import (
    DiscoveryAudience,
    DiscoveryBookFormat,
    DiscoveryCandidate,
    DiscoveryContext,
    DiscoveryPainPoint,
    DiscoveryRun,
    DiscoveryTopic,
)
from app.models.keyword import Keyword
from app.models.niche import NicheCluster
from app.models.report import Report
from app.schemas.analysis import NicheClusterAnalysisRead
from app.schemas.discovery import (
    DiscoveryCandidateRead,
    DiscoveryCycleRead,
    DiscoveryGenerateRead,
    DiscoveryUniverseItemRead,
    DiscoveryUniverseRead,
)
from app.schemas.sachbuch import SachbuchAnalysisRead
from app.services.ai_intelligence import semantic_key_for_candidate_phrase, semantic_text_similarity
from app.services.book_filters import has_non_book_markers, is_probable_book_record
from app.services.keyword_intelligence import infer_keyword_intelligence
from app.services.niche_cluster_analysis import build_and_analyze_seed_cluster
from app.services.pipeline_orchestration import run_seed_pipeline
from app.services.report_builder import generate_cluster_report
from app.services.sachbuch_analysis import analyze_sachbuch_cluster
from app.services.scoring_engine import clamp
from app.services.signal_generation import build_candidate_signals
from app.services.text_utils import normalize_text


DEFAULT_TOPICS = [
    {
        "name": "Pflege",
        "slug": "pflege",
        "description": "Pflegeorganisation, Dokumentation und Familienalltag.",
        "category_hint": "Gesundheit und Dokumentation",
        "book_type_hint": "sachbuch",
        "risk_level": "medium",
        "priority": 96,
    },
    {
        "name": "Blutdruck",
        "slug": "blutdruck",
        "description": "Selbstbeobachtung und Alltagstracking.",
        "category_hint": "Gesundheit und Dokumentation",
        "book_type_hint": "medium_content",
        "risk_level": "medium",
        "priority": 93,
    },
    {
        "name": "Blutzucker",
        "slug": "blutzucker",
        "description": "Messroutinen, Dokumentation und Verlauf.",
        "category_hint": "Gesundheit und Dokumentation",
        "book_type_hint": "medium_content",
        "risk_level": "medium",
        "priority": 88,
    },
    {
        "name": "ADHS",
        "slug": "adhs",
        "description": "Struktur, Alltagsorganisation und Selbstmanagement.",
        "category_hint": "Selbsthilfe und mentale Gesundheit",
        "book_type_hint": "sachbuch",
        "risk_level": "medium",
        "priority": 94,
    },
    {
        "name": "Haushalt",
        "slug": "haushalt",
        "description": "Alltagsorganisation, Listen und Routinen.",
        "category_hint": "Familie und Alltag",
        "book_type_hint": "medium_content",
        "risk_level": "low",
        "priority": 82,
    },
    {
        "name": "Pflegegrad-Antrag",
        "slug": "pflegegrad-antrag",
        "description": "Antraege, Unterlagen und Behordengaenge.",
        "category_hint": "Gesundheit und Dokumentation",
        "book_type_hint": "sachbuch",
        "risk_level": "medium",
        "priority": 91,
    },
    {
        "name": "Hundegesundheit",
        "slug": "hundegesundheit",
        "description": "Symptombeobachtung und Tieralltag.",
        "category_hint": "Hobby und Freizeit",
        "book_type_hint": "medium_content",
        "risk_level": "low",
        "priority": 80,
    },
    {
        "name": "Schichtarbeit",
        "slug": "schichtarbeit",
        "description": "Rhythmus, Routinen und Belastungssteuerung.",
        "category_hint": "Beruf und Business",
        "book_type_hint": "medium_content",
        "risk_level": "low",
        "priority": 78,
    },
    {
        "name": "Nebengewerbe",
        "slug": "nebengewerbe",
        "description": "Einstieg, Struktur und Kleinunternehmeralltag.",
        "category_hint": "Beruf und Business",
        "book_type_hint": "sachbuch",
        "risk_level": "medium",
        "priority": 84,
    },
    {
        "name": "KI im Handwerk",
        "slug": "ki-im-handwerk",
        "description": "Praktische KI-Anwendung fuer kleine Betriebe.",
        "category_hint": "Beruf und Business",
        "book_type_hint": "sachbuch",
        "risk_level": "medium",
        "priority": 86,
    },
    {
        "name": "Behordenpost",
        "slug": "behoerdenpost",
        "description": "Briefe, Fristen und private Ordnung.",
        "category_hint": "Familie und Alltag",
        "book_type_hint": "medium_content",
        "risk_level": "low",
        "priority": 76,
    },
    {
        "name": "Trauer",
        "slug": "trauer",
        "description": "Selbsthilfe, Begleitung und Orientierung.",
        "category_hint": "Selbsthilfe und mentale Gesundheit",
        "book_type_hint": "sachbuch",
        "risk_level": "medium",
        "priority": 73,
    },
    {
        "name": "Lernorganisation",
        "slug": "lernorganisation",
        "description": "Pruefungsvorbereitung, Fokus und Lernplanung.",
        "category_hint": "Lernen und Bildung",
        "book_type_hint": "medium_content",
        "risk_level": "low",
        "priority": 81,
    },
]

DEFAULT_AUDIENCES = [
    {"name": "Senioren", "slug": "senioren", "description": "Aeltere Leser mit klarer Alltagssituation.", "priority": 90},
    {"name": "Angehoerige", "slug": "angehoerige", "description": "Familienmitglieder mit Betreuungs- und Organisationsbedarf.", "priority": 96},
    {"name": "Eltern", "slug": "eltern", "description": "Eltern mit Organisations- oder Begleitaufgaben.", "priority": 86},
    {"name": "Selbststaendige", "slug": "selbststaendige", "description": "Solo-Selbststaendige mit Zeitdruck und Strukturbedarf.", "priority": 84},
    {"name": "Handwerker", "slug": "handwerker", "description": "Kleine Betriebe und operative Teams.", "priority": 83},
    {"name": "Lehrer", "slug": "lehrer", "description": "Berufsalltag mit hoher Planungsdichte.", "priority": 72},
    {"name": "Hundehalter", "slug": "hundehalter", "description": "Tierhalter mit Beobachtungs- und Routinenthemen.", "priority": 78},
    {"name": "Studierende", "slug": "studierende", "description": "Junge Erwachsene mit Lern- und Organisationsbedarf.", "priority": 74},
    {"name": "Erwachsene mit ADHS", "slug": "erwachsene-mit-adhs", "description": "Klare Zielgruppe fuer Struktur- und Routinenangebote.", "priority": 92},
    {"name": "Alleinerziehende", "slug": "alleinerziehende", "description": "Haushalts- und Familienorganisation unter Zeitdruck.", "priority": 79},
    {"name": "Schichtarbeiter", "slug": "schichtarbeiter", "description": "Berufsalltag mit wechselnden Routinen.", "priority": 71},
]

DEFAULT_PAIN_POINTS = [
    {"name": "Dokumentation", "slug": "dokumentation", "description": "Informationen sauber festhalten.", "priority": 94},
    {"name": "Ueberforderung", "slug": "ueberforderung", "description": "Zu viel Komplexitaet ohne klare Struktur.", "priority": 89},
    {"name": "Zeitmangel", "slug": "zeitmangel", "description": "Wenig Zeit fuer Recherche und Umsetzung.", "priority": 88},
    {"name": "Angst vor Fehlern", "slug": "angst-vor-fehlern", "description": "Hoher Druck, nichts falsch zu machen.", "priority": 87},
    {"name": "fehlende Struktur", "slug": "fehlende-struktur", "description": "Ablauf und Reihenfolge sind unklar.", "priority": 91},
    {"name": "Buerokratie", "slug": "buerokratie", "description": "Antraege, Nachweise und Verwaltungslast.", "priority": 86},
    {"name": "Alltag organisieren", "slug": "alltag-organisieren", "description": "Wiederkehrende Routinen greifbar machen.", "priority": 84},
    {"name": "Symptome beobachten", "slug": "symptome-beobachten", "description": "Verlaeufe und Hinweise systematisch tracken.", "priority": 82},
    {"name": "Routinen aufbauen", "slug": "routinen-aufbauen", "description": "Verhalten sauber einueben und halten.", "priority": 80},
]

DEFAULT_CONTEXTS = [
    {"name": "nach Krankenhausentlassung", "slug": "nach-krankenhausentlassung", "description": "Hoher Informations- und Strukturbedarf nach Entlassung.", "priority": 95},
    {"name": "im Alltag", "slug": "im-alltag", "description": "Alltaeglicher Einsatz mit wenig Reibung.", "priority": 84},
    {"name": "fuer Einsteiger", "slug": "fuer-einsteiger", "description": "No-Vorwissen, niedrige Einstiegshuerde.", "priority": 86},
    {"name": "im Familienalltag", "slug": "im-familienalltag", "description": "Mehrere Rollen und wenig Zeit.", "priority": 82},
    {"name": "im Berufsalltag", "slug": "im-berufsalltag", "description": "Praxisnahe Anwendung waehrend der Arbeit.", "priority": 80},
    {"name": "bei Behoerden", "slug": "bei-behoerden", "description": "Formulare, Fristen und Nachweise.", "priority": 88},
    {"name": "fuer Zuhause", "slug": "fuer-zuhause", "description": "Nutzung ohne professionelle Umgebung.", "priority": 74},
    {"name": "waehrend Schichtarbeit", "slug": "waehrend-schichtarbeit", "description": "Wechselnde Routinen und begrenzte Energie.", "priority": 70},
    {"name": "vor dem Pflegegrad-Antrag", "slug": "vor-dem-pflegegrad-antrag", "description": "Vorbereitung auf Dokumentation und Antragstellung.", "priority": 90},
    {"name": "mit wenig Zeit", "slug": "mit-wenig-zeit", "description": "Schnelle Nutzbarkeit ohne Theorieballast.", "priority": 79},
]

DEFAULT_BOOK_FORMATS = [
    {"name": "Tagebuch", "slug": "tagebuch", "description": "Fortlaufende Selbstbeobachtung und Eintragungen.", "book_type_hint": "medium_content", "priority": 90},
    {"name": "Planer", "slug": "planer", "description": "Struktur und Terminlogik.", "book_type_hint": "medium_content", "priority": 88},
    {"name": "Arbeitsbuch", "slug": "arbeitsbuch", "description": "Umsetzungsorientierte Aufgaben und Uebungen.", "book_type_hint": "medium_content", "priority": 82},
    {"name": "Checklistenbuch", "slug": "checklistenbuch", "description": "Schnell nutzbare Schrittfolgen und Vorlagen.", "book_type_hint": "medium_content", "priority": 96},
    {"name": "Leitfaden", "slug": "leitfaden", "description": "Praxisratgeber mit klarer Orientierung.", "book_type_hint": "sachbuch", "priority": 87},
    {"name": "Vorlagenbuch", "slug": "vorlagenbuch", "description": "Sammlung direkt nutzbarer Vorlagen.", "book_type_hint": "medium_content", "priority": 85},
    {"name": "Workbook", "slug": "workbook", "description": "Angeleitete Umsetzung mit Reflexionsanteil.", "book_type_hint": "sachbuch", "priority": 78},
    {"name": "Tracker", "slug": "tracker", "description": "Mess- und Fortschrittsverfolgung.", "book_type_hint": "medium_content", "priority": 84},
    {"name": "Ordner", "slug": "ordner", "description": "Dokumenten- und Uebersichtsstruktur.", "book_type_hint": "medium_content", "priority": 91},
    {"name": "Praxisbuch", "slug": "praxisbuch", "description": "Mehr Tiefe als ein Template, aber klar an der Anwendung.", "book_type_hint": "sachbuch", "priority": 80},
]

ADDITIONAL_BOOK_FORMATS = [
    {"name": "Handbuch", "slug": "handbuch", "description": "Vertieftes Praxis- und Referenzwissen.", "book_type_hint": "sachbuch", "priority": 89},
    {"name": "Kochbuch", "slug": "kochbuch", "description": "Praxisnahe Rezepte und Anwendungsroutinen.", "book_type_hint": "sachbuch", "priority": 83},
    {"name": "Sammlung", "slug": "sammlung", "description": "Kuratiertes Material fuer ein klar abgegrenztes Thema.", "book_type_hint": "sachbuch", "priority": 76},
]

TOPIC_ALLOWED_AUDIENCE_SLUGS = {
    "pflege": {"angehoerige", "senioren", "eltern"},
    "blutdruck": {"senioren", "angehoerige"},
    "blutzucker": {"senioren", "angehoerige"},
    "adhs": {"erwachsene-mit-adhs", "eltern", "studierende"},
    "haushalt": {"erwachsene-mit-adhs", "eltern", "alleinerziehende", "senioren"},
    "pflegegrad-antrag": {"angehoerige", "senioren"},
    "hundegesundheit": {"hundehalter"},
    "schichtarbeit": {"schichtarbeiter", "handwerker"},
    "nebengewerbe": {"selbststaendige", "handwerker", "studierende"},
    "ki-im-handwerk": {"handwerker", "selbststaendige"},
    "behoerdenpost": {"angehoerige", "senioren", "alleinerziehende", "selbststaendige"},
    "trauer": {"angehoerige", "eltern"},
    "lernorganisation": {"studierende", "erwachsene-mit-adhs", "eltern", "lehrer"},
}

CONTEXT_ALLOWED_TOPIC_SLUGS = {
    "nach-krankenhausentlassung": {"pflege", "pflegegrad-antrag", "blutdruck", "blutzucker"},
    "vor-dem-pflegegrad-antrag": {"pflege", "pflegegrad-antrag", "behoerdenpost"},
    "waehrend-schichtarbeit": {"schichtarbeit", "nebengewerbe", "ki-im-handwerk"},
    "bei-behoerden": {"pflegegrad-antrag", "behoerdenpost", "pflege", "nebengewerbe"},
}

RECENT_VALIDATION_REUSE_HOURS = 24
DISCOVERY_DYNAMIC_TOPIC_LIMIT = 96
DISCOVERY_DYNAMIC_TOPIC_STOPWORDS = {
    "das",
    "der",
    "die",
    "dem",
    "den",
    "des",
    "ein",
    "eine",
    "einer",
    "eines",
    "und",
    "oder",
    "mit",
    "ohne",
    "von",
    "vom",
    "zum",
    "zur",
    "im",
    "in",
    "am",
    "an",
    "bei",
    "nach",
    "vor",
    "fuer",
    "mein",
    "dein",
    "euer",
    "unser",
    "für",
}
DISCOVERY_DYNAMIC_TOPIC_NOISE = {
    "buch",
    "reihe",
    "edition",
    "kompakt",
    "ultimativ",
    "komplett",
    "einfach",
    "praxis",
    "wissenschaftliches",
    "leserfreundlicher",
    "praxisnah",
    "freundlicher",
    "form",
    "zusammengefasst",
    "symphonie",
    "psyche",
    "ergebnisse",
    "studien",
    "study",
    "guide",
    "edition",
    "tools",
    "begleiter",
    "praktische",
    "praktischer",
    "praktisches",
}
DISCOVERY_NON_BOOK_TOKENS = {
    "geraete",
    "gerate",
    "geräte",
    "pillen",
    "kapseln",
    "tabletten",
    "protein",
    "booster",
    "pulver",
    "caps",
    "capsules",
    "headband",
    "wearable",
    "sensor",
    "shaker",
    "ampullen",
    "bundle",
}
DISCOVERY_DYNAMIC_FORMAT_TOKENS = {
    "buch",
    "handbuch",
    "kochbuch",
    "tagebuch",
    "tracker",
    "planer",
    "journal",
    "logbuch",
    "ratgeber",
    "leitfaden",
    "praxisbuch",
    "arbeitsbuch",
    "ubungsbuch",
    "uebungsbuch",
    "workbook",
    "checklistenbuch",
    "vorlagenbuch",
    "ordner",
    "sammlung",
    "texte",
    "textesammlung",
    "notizbuch",
}
DISCOVERY_COMPOUND_FORMAT_SUFFIXES = {
    "arbeitsbuch",
    "checklistenbuch",
    "handbuch",
    "journal",
    "kochbuch",
    "leitfaden",
    "logbuch",
    "notizbuch",
    "ordner",
    "planer",
    "praxisbuch",
    "ratgeber",
    "sammlung",
    "tagebuch",
    "textesammlung",
    "tracker",
    "vorlagenbuch",
    "workbook",
    "ubungsbuch",
    "uebungsbuch",
}
DISCOVERY_DYNAMIC_BREAK_MARKERS = (
    " fuer ",
    " für ",
    " mit ",
    " im ",
    " bei ",
    " nach ",
    " vor ",
    " waehrend ",
    " während ",
    " ohne ",
    " zum ",
    " zur ",
)
DISCOVERY_TRACKING_TOPIC_TOKENS = {
    "blutdruck",
    "blutzucker",
    "pflege",
    "pflegegrad",
    "haushalt",
    "schichtarbeit",
    "behoerdenpost",
    "behordenpost",
    "lernorganisation",
    "adhs",
}
DISCOVERY_MEDIUM_CONTENT_FORMAT_SLUGS = {
    "tagebuch",
    "planer",
    "arbeitsbuch",
    "checklistenbuch",
    "vorlagenbuch",
    "tracker",
    "ordner",
}
DISCOVERY_REFERENCE_FORMAT_SLUGS = {"leitfaden", "praxisbuch", "workbook", "handbuch", "kochbuch", "sammlung"}
DISCOVERY_GENERIC_TOPIC_PHRASES = {
    "eintragen der messwerte",
    "platz",
    "uebersichtliches format",
    "vorgedruckte seiten",
}
DISCOVERY_GENERIC_TOPIC_TOKENS = {
    "alltag",
    "begleiter",
    "eintragen",
    "format",
    "messwerte",
    "platz",
    "seiten",
    "schrift",
    "struktur",
    "tools",
    "uebersichtliches",
    "vorgedruckte",
}
DISCOVERY_PAIN_POINT_SUFFIXES = {
    "ueberforderung": "einfach erklaert",
    "zeitmangel": "mit wenig Zeit",
    "angst vor fehlern": "fuer sichere Anwendung",
    "fehlende struktur": "mit klarer Struktur",
    "buerokratie": "bei Antraegen",
    "alltag organisieren": "fuer den Alltag",
    "symptome beobachten": "zur Verlaufskontrolle",
    "routinen aufbauen": "fuer Routinen",
}
DISCOVERY_SUFFIX_BLOCKED_FORMATS = {"tagebuch", "tracker", "ordner", "vorlagenbuch", "checklistenbuch", "planer"}


@dataclass(frozen=True)
class CandidateSpec:
    topic_id: int
    audience_id: int | None
    pain_point_id: int | None
    context_id: int | None
    book_format_id: int | None
    candidate_phrase: str
    normalized_phrase: str
    semantic_key: str | None
    semantic_family: str | None
    book_type_hint: str | None
    risk_level: str | None
    generation_score: int
    specificity_score: int
    intent_score: int
    audience_clarity_score: int
    format_suitability_score: int
    competition_probability_score: int
    production_effort_score: int
    pain_clarity_score: int


@dataclass
class GenerationBatch:
    run: DiscoveryRun
    created_count: int
    updated_count: int
    deduplicated_count: int
    candidates: list[DiscoveryCandidate]


def ensure_default_discovery_universe(db: Session) -> None:
    try:
        harvested_dynamic_topics = _harvest_dynamic_topic_rows(db)
        harvested_dynamic_slugs = {row["slug"] for row in harvested_dynamic_topics}
        _upsert_universe_rows(db, DiscoveryTopic, DEFAULT_TOPICS)
        _upsert_universe_rows(db, DiscoveryAudience, DEFAULT_AUDIENCES)
        _upsert_universe_rows(db, DiscoveryPainPoint, DEFAULT_PAIN_POINTS)
        _upsert_universe_rows(db, DiscoveryContext, DEFAULT_CONTEXTS)
        _upsert_universe_rows(db, DiscoveryBookFormat, DEFAULT_BOOK_FORMATS)
        _upsert_universe_rows(db, DiscoveryBookFormat, ADDITIONAL_BOOK_FORMATS)
        _deactivate_invalid_dynamic_topics(db, harvested_dynamic_slugs)
        _upsert_universe_rows(db, DiscoveryTopic, harvested_dynamic_topics)
        _deactivate_invalid_dynamic_topics(db, harvested_dynamic_slugs)
        _prune_invalid_generated_candidates(db)
        db.commit()
    except IntegrityError:
        db.rollback()


def list_discovery_universe(db: Session) -> DiscoveryUniverseRead:
    ensure_default_discovery_universe(db)
    return DiscoveryUniverseRead(
        topics=_serialize_universe_items(_active_rows(db, DiscoveryTopic)),
        audiences=_serialize_universe_items(_active_rows(db, DiscoveryAudience)),
        pain_points=_serialize_universe_items(_active_rows(db, DiscoveryPainPoint)),
        contexts=_serialize_universe_items(_active_rows(db, DiscoveryContext)),
        book_formats=_serialize_universe_items(_active_rows(db, DiscoveryBookFormat)),
    )


def list_discovery_candidates(
    db: Session,
    *,
    limit: int = 40,
    status: str | None = None,
) -> list[DiscoveryCandidateRead]:
    ensure_default_discovery_universe(db)
    statement = select(DiscoveryCandidate)
    if status:
        statement = statement.where(DiscoveryCandidate.status == status)
    else:
        statement = statement.where(DiscoveryCandidate.status != "discarded")
    candidates = list(
        db.scalars(
            statement.order_by(
                DiscoveryCandidate.final_opportunity_score.desc().nullslast(),
                DiscoveryCandidate.generation_score.desc().nullslast(),
                DiscoveryCandidate.updated_at.desc(),
                DiscoveryCandidate.id.desc(),
            ).limit(max(120, limit * 8))
        )
    )
    eligible_candidates = _filter_eligible_candidates(db, candidates)
    return _serialize_candidates(db, _select_ranked_candidates(eligible_candidates, limit=limit))


def get_discovery_candidate(db: Session, candidate_id: int) -> DiscoveryCandidateRead:
    candidate = db.get(DiscoveryCandidate, candidate_id)
    if candidate is None:
        raise ValueError("Discovery candidate not found.")
    return _serialize_candidates(db, [candidate])[0]


def generate_discovery_candidates(
    db: Session,
    *,
    limit: int = 120,
) -> DiscoveryGenerateRead:
    run = _create_run(
        db,
        mode="generate",
        requested_generate_limit=limit,
        requested_validate_limit=0,
        auto_generate_reports=False,
        notes="Generated discovery candidates from the seed universe.",
    )
    batch = _generate_candidate_batch(db, run, limit=limit)
    run.status = "completed"
    run.generated_count = batch.created_count
    run.kept_count = len(batch.candidates)
    db.add(run)
    db.commit()
    return DiscoveryGenerateRead(
        run_id=run.id,
        generated_count=batch.created_count,
        updated_count=batch.updated_count,
        deduplicated_count=batch.deduplicated_count,
        candidates=_serialize_candidates(db, batch.candidates),
    )


def validate_discovery_candidate(
    db: Session,
    candidate_id: int,
    *,
    force: bool = False,
    auto_generate_reports: bool = False,
) -> DiscoveryCandidateRead:
    candidate = db.get(DiscoveryCandidate, candidate_id)
    if candidate is None:
        raise ValueError("Discovery candidate not found.")

    if _can_reuse_validation(candidate, force=force):
        return _serialize_candidates(db, [candidate])[0]

    run = _create_run(
        db,
        mode="validate",
        requested_generate_limit=0,
        requested_validate_limit=1,
        auto_generate_reports=auto_generate_reports,
        notes=f"Validated discovery candidate {candidate.candidate_phrase}.",
    )

    try:
        _validate_candidate(db, candidate, run=run, auto_generate_reports=auto_generate_reports)
    except Exception as exc:
        db.rollback()
        failed_run = db.get(DiscoveryRun, run.id)
        if failed_run is not None:
            failed_run.status = "failed"
            failed_run.notes = str(exc)[:500]
            db.add(failed_run)
        failed_candidate = db.get(DiscoveryCandidate, candidate_id)
        if failed_candidate is not None:
            failed_candidate.status = "failed"
            failed_candidate.validation_notes = str(exc)[:500]
            db.add(failed_candidate)
        db.commit()
        raise

    completed_run = db.get(DiscoveryRun, run.id)
    if completed_run is not None:
        completed_run.status = "completed"
        db.add(completed_run)
        db.commit()

    return _serialize_candidates(db, [db.get(DiscoveryCandidate, candidate_id)])[0]


def run_discovery_cycle(
    db: Session,
    *,
    generate_limit: int = 120,
    validate_limit: int = 6,
    auto_generate_reports: bool = True,
    force: bool = False,
) -> DiscoveryCycleRead:
    run = _create_run(
        db,
        mode="cycle",
        requested_generate_limit=generate_limit,
        requested_validate_limit=validate_limit,
        auto_generate_reports=auto_generate_reports,
        notes="Generated, filtered, and validated a discovery batch.",
    )
    batch = _generate_candidate_batch(db, run, limit=generate_limit)
    pending_candidates = _select_candidates_for_validation(
        db,
        limit=validate_limit,
        force=force,
    )

    validated_candidates: list[DiscoveryCandidate] = []
    failed_count = 0
    report_count = 0
    for candidate in pending_candidates:
        try:
            _validate_candidate(
                db,
                candidate,
                run=run,
                auto_generate_reports=auto_generate_reports,
            )
            db.refresh(candidate)
            validated_candidates.append(candidate)
            report_count += candidate.report_count
        except Exception as exc:
            failed_count += 1
            db.rollback()
            failed_candidate = db.get(DiscoveryCandidate, candidate.id)
            if failed_candidate is not None:
                failed_candidate.status = "failed"
                failed_candidate.validation_notes = str(exc)[:500]
                db.add(failed_candidate)
                db.commit()

    run.status = "completed"
    run.generated_count = batch.created_count
    run.validated_count = len(validated_candidates)
    run.kept_count = sum(1 for candidate in validated_candidates if candidate.decision == "GO")
    run.notes = (
        f"Deduplicated {batch.deduplicated_count} ideas, validated {len(validated_candidates)}, "
        f"failed {failed_count}."
    )
    db.add(run)
    db.commit()

    return DiscoveryCycleRead(
        run_id=run.id,
        generated_count=batch.created_count,
        updated_count=batch.updated_count,
        deduplicated_count=batch.deduplicated_count,
        validated_count=len(validated_candidates),
        kept_count=run.kept_count,
        failed_count=failed_count,
        report_count=report_count,
        candidates=_serialize_candidates(db, validated_candidates),
    )


def _active_rows(db: Session, model: type[object]) -> list[object]:
    return list(
        db.scalars(
            select(model)
            .where(getattr(model, "active") == True)  # noqa: E712
            .order_by(getattr(model, "priority").desc(), getattr(model, "name").asc())
        )
    )


def _upsert_universe_rows(db: Session, model: type[object], rows: list[dict[str, object]]) -> None:
    existing = {
        item.slug: item
        for item in db.scalars(select(model))
    }
    for row in rows:
        current = existing.get(row["slug"])
        if current is None:
            current = model(**row)
            db.add(current)
            existing[row["slug"]] = current
            continue
        for field_name, value in row.items():
            setattr(current, field_name, value)
        current.active = True
        db.add(current)


def _harvest_dynamic_topic_rows(
    db: Session,
    *,
    limit: int = DISCOVERY_DYNAMIC_TOPIC_LIMIT,
) -> list[dict[str, object]]:
    default_slugs = {_canonical_discovery_slug(row["slug"]) for row in DEFAULT_TOPICS}
    topic_scores: Counter[str] = Counter()
    topic_meta: dict[str, dict[str, object]] = {}

    keywords = list(
        db.scalars(
            select(Keyword)
            .where(Keyword.seed_keyword_id.is_(None))
            .order_by(Keyword.priority.desc(), Keyword.id.asc())
            .limit(500)
        )
    )
    for keyword in keywords:
        source_text = keyword.keyword or ""
        if not source_text or has_non_book_markers(source_text):
            continue
        source_book_type = keyword.book_type or _book_type_hint_from_source_text(source_text)
        intelligence = infer_keyword_intelligence(source_text, book_type=source_book_type)
        for candidate in _extract_topic_candidates_from_text(source_text, allow_full_phrase=True):
            _record_dynamic_topic_candidate(
                topic_scores,
                topic_meta,
                candidate,
                source_text=source_text,
                weight=max(18, keyword.priority or 0),
                book_type_hint=source_book_type or _book_type_hint_from_intent(intelligence.search_intent_family),
                category_hint=keyword.category_hint or intelligence.category_hint,
                risk_level=keyword.risk_level or intelligence.risk_level,
            )

    cluster_keywords = list(
        db.scalars(
            select(NicheCluster.main_keyword)
            .where(NicheCluster.main_keyword.is_not(None))
            .order_by(NicheCluster.updated_at.desc(), NicheCluster.id.desc())
            .limit(250)
        )
    )
    for cluster_keyword in cluster_keywords:
        source_text = cluster_keyword or ""
        if not source_text or has_non_book_markers(source_text):
            continue
        source_book_type = _book_type_hint_from_source_text(source_text)
        intelligence = infer_keyword_intelligence(source_text, book_type=source_book_type)
        for candidate in _extract_topic_candidates_from_text(source_text, allow_full_phrase=True):
            _record_dynamic_topic_candidate(
                topic_scores,
                topic_meta,
                candidate,
                source_text=source_text,
                weight=42,
                book_type_hint=source_book_type or _book_type_hint_from_intent(intelligence.search_intent_family),
                category_hint=intelligence.category_hint,
                risk_level=intelligence.risk_level,
            )

    books = list(
        db.scalars(
            select(Book)
            .where(Book.title.is_not(None))
            .order_by(Book.updated_at.desc(), Book.id.desc())
            .limit(400)
        )
    )
    for book in books:
        if not is_probable_book_record(book):
            continue
        source_text = book.title or ""
        if not source_text:
            continue
        detail_text = " - ".join(part for part in [book.title, book.subtitle] if part)
        source_book_type = book.book_class or _book_type_hint_from_source_text(source_text)
        intelligence = infer_keyword_intelligence(detail_text, book_type=source_book_type)
        for candidate in _extract_topic_candidates_from_text(source_text, primary_only=True):
            _record_dynamic_topic_candidate(
                topic_scores,
                topic_meta,
                candidate,
                source_text=detail_text,
                weight=28 if book.book_class else 20,
                book_type_hint=source_book_type or _book_type_hint_from_intent(intelligence.search_intent_family),
                category_hint=intelligence.category_hint,
                risk_level=intelligence.risk_level,
            )

    rows: list[dict[str, object]] = []
    seen_slugs: set[str] = set()
    for normalized_phrase, aggregate_score in topic_scores.most_common(limit * 4):
        meta = topic_meta[normalized_phrase]
        topic_name = str(meta["name"])
        slug = _slugify_discovery_value(topic_name)
        canonical_slug = _canonical_discovery_slug(slug)
        if not slug or canonical_slug in default_slugs or canonical_slug in seen_slugs:
            continue
        if not _dynamic_topic_meets_support_threshold(
            topic_name,
            aggregate_score=aggregate_score,
            hit_count=int(meta.get("hit_count", 1)),
        ):
            continue

        source_text = str(meta.get("source_text") or topic_name)
        book_type_hint = (
            meta.get("book_type_hint")
            or _book_type_hint_from_source_text(source_text)
            or _book_type_hint_from_source_text(topic_name)
        )
        intelligence = infer_keyword_intelligence(topic_name, book_type=book_type_hint)
        if not _is_valid_topic_candidate(topic_name):
            continue

        rows.append(
            {
                "name": topic_name,
                "slug": slug,
                "description": "Auto-harvested from live keyword, cluster, and book corpus.",
                "category_hint": meta.get("category_hint") or intelligence.category_hint,
                "book_type_hint": book_type_hint,
                "risk_level": meta.get("risk_level") or intelligence.risk_level,
                "priority": clamp(40 + min(55, round(aggregate_score / 2))),
            }
        )
        seen_slugs.add(canonical_slug)
        if len(rows) >= limit:
            break

    return rows


def _deactivate_invalid_dynamic_topics(db: Session, harvested_dynamic_slugs: set[str] | None = None) -> None:
    default_slugs = {row["slug"] for row in DEFAULT_TOPICS}
    for topic in db.scalars(select(DiscoveryTopic)):
        if topic.slug in default_slugs:
            continue
        topic.active = _is_valid_topic_candidate(topic.name) and (
            harvested_dynamic_slugs is None or topic.slug in harvested_dynamic_slugs
        )
        db.add(topic)


def _prune_invalid_generated_candidates(db: Session) -> None:
    topics = {topic.id: topic for topic in db.scalars(select(DiscoveryTopic))}
    audiences = {audience.id: audience for audience in db.scalars(select(DiscoveryAudience))}
    pain_points = {pain_point.id: pain_point for pain_point in db.scalars(select(DiscoveryPainPoint))}
    contexts = {context.id: context for context in db.scalars(select(DiscoveryContext))}
    formats = {book_format.id: book_format for book_format in db.scalars(select(DiscoveryBookFormat))}

    for candidate in db.scalars(select(DiscoveryCandidate).where(DiscoveryCandidate.status == "generated")):
        topic = topics.get(candidate.topic_id)
        audience = audiences.get(candidate.audience_id) if candidate.audience_id else None
        pain_point = pain_points.get(candidate.pain_point_id) if candidate.pain_point_id else None
        context = contexts.get(candidate.context_id) if candidate.context_id else None
        book_format = formats.get(candidate.book_format_id) if candidate.book_format_id else None
        if (
            topic is None
            or book_format is None
            or not topic.active
            or not _is_valid_topic_candidate(topic.name)
            or has_non_book_markers(candidate.candidate_phrase)
            or not _is_topic_format_pair_supported(topic, book_format, pain_point)
            or not _is_topic_audience_pair_supported(topic, audience)
            or not _is_topic_context_pair_supported(topic, context)
        ):
            candidate.status = "discarded"
            candidate.validation_notes = "Discarded by discovery quality filters."
            db.add(candidate)


def _filter_eligible_candidates(
    db: Session,
    candidates: list[DiscoveryCandidate],
) -> list[DiscoveryCandidate]:
    if not candidates:
        return []

    topics = {topic.id: topic for topic in db.scalars(select(DiscoveryTopic))}
    audiences = {audience.id: audience for audience in db.scalars(select(DiscoveryAudience))}
    pain_points = {pain_point.id: pain_point for pain_point in db.scalars(select(DiscoveryPainPoint))}
    contexts = {context.id: context for context in db.scalars(select(DiscoveryContext))}
    formats = {book_format.id: book_format for book_format in db.scalars(select(DiscoveryBookFormat))}

    eligible: list[DiscoveryCandidate] = []
    for candidate in candidates:
        topic = topics.get(candidate.topic_id)
        audience = audiences.get(candidate.audience_id) if candidate.audience_id else None
        pain_point = pain_points.get(candidate.pain_point_id) if candidate.pain_point_id else None
        context = contexts.get(candidate.context_id) if candidate.context_id else None
        book_format = formats.get(candidate.book_format_id) if candidate.book_format_id else None
        if (
            topic is None
            or book_format is None
            or not topic.active
            or not book_format.active
            or not _is_valid_topic_candidate(topic.name)
            or has_non_book_markers(candidate.candidate_phrase)
            or not _is_topic_format_pair_supported(topic, book_format, pain_point)
            or not _is_topic_audience_pair_supported(topic, audience)
            or not _is_topic_context_pair_supported(topic, context)
        ):
            continue
        eligible.append(candidate)
    return eligible


def _record_dynamic_topic_candidate(
    topic_scores: Counter[str],
    topic_meta: dict[str, dict[str, object]],
    candidate: str,
    *,
    source_text: str,
    weight: int,
    book_type_hint: str | None,
    category_hint: str | None,
    risk_level: str | None,
) -> None:
    topic_name = normalize_text(candidate)
    if topic_name is None or not _is_valid_topic_candidate(topic_name):
        return

    normalized = _normalize_phrase(topic_name)
    topic_scores[normalized] += max(1, weight)
    current = topic_meta.get(normalized)
    if current is None or weight >= int(current.get("weight", 0)):
        topic_meta[normalized] = {
            "name": topic_name,
            "source_text": source_text,
            "book_type_hint": book_type_hint,
            "category_hint": category_hint,
            "risk_level": risk_level,
            "weight": weight,
            "hit_count": 1 if current is None else int(current.get("hit_count", 1)) + 1,
        }
        return

    current["hit_count"] = int(current.get("hit_count", 1)) + 1
    if current.get("book_type_hint") is None and book_type_hint is not None:
        current["book_type_hint"] = book_type_hint
    if current.get("category_hint") is None and category_hint is not None:
        current["category_hint"] = category_hint
    if current.get("risk_level") is None and risk_level is not None:
        current["risk_level"] = risk_level


def _dynamic_topic_meets_support_threshold(
    topic_name: str,
    *,
    aggregate_score: int,
    hit_count: int,
) -> bool:
    if hit_count >= 2:
        return True

    tokens = _normalize_phrase(topic_name).split()
    if len(tokens) <= 1:
        return aggregate_score >= 70
    if len(tokens) >= 3:
        return aggregate_score >= 70
    return aggregate_score >= 42


def _extract_topic_candidates_from_text(
    value: str,
    *,
    allow_full_phrase: bool = False,
    primary_only: bool = False,
) -> list[str]:
    normalized = normalize_text(value) or value
    if not normalized:
        return []

    split_fragments = [
        fragment.strip()
        for fragment in re.split(r"\s(?:-+|–|—|:|\|)\s", normalized)
        if fragment and fragment.strip()
    ]
    candidate_inputs = split_fragments[:3] if split_fragments else [normalized]
    if allow_full_phrase:
        candidate_inputs = [normalized, *candidate_inputs]
    if primary_only:
        candidate_inputs = candidate_inputs[:1]

    candidates: list[str] = []
    seen: set[str] = set()
    for candidate_input in candidate_inputs:
        cleaned = _clean_topic_fragment(candidate_input)
        if cleaned is None:
            continue
        normalized_cleaned = _normalize_phrase(cleaned)
        if normalized_cleaned in seen or not _is_valid_topic_candidate(cleaned):
            continue
        seen.add(normalized_cleaned)
        candidates.append(cleaned)
    return candidates


def _clean_topic_fragment(value: str) -> str | None:
    text = (normalize_text(value) or value).strip(" -:|/,")
    if not text:
        return None

    lowered = text.casefold()
    for marker in DISCOVERY_DYNAMIC_BREAK_MARKERS:
        index = lowered.find(marker)
        if index > 0:
            text = text[:index].strip(" -:|/,")
            lowered = text.casefold()
            break

    raw_tokens = [
        token.strip(" -:|/,().[]{}!?\"'")
        for token in text.split()
        if token.strip(" -:|/,().[]{}!?\"'")
    ]
    while raw_tokens and _normalize_discovery_token(raw_tokens[0]) in DISCOVERY_DYNAMIC_TOPIC_STOPWORDS:
        raw_tokens.pop(0)
    while raw_tokens and _normalize_discovery_token(raw_tokens[-1]) in (
        DISCOVERY_DYNAMIC_TOPIC_STOPWORDS | DISCOVERY_DYNAMIC_TOPIC_NOISE | DISCOVERY_DYNAMIC_FORMAT_TOKENS
    ):
        raw_tokens.pop()
    while raw_tokens and _normalize_discovery_token(raw_tokens[0]) in DISCOVERY_DYNAMIC_TOPIC_NOISE:
        raw_tokens.pop(0)
    raw_tokens = _collapse_topic_tokens(raw_tokens)

    cleaned = normalize_text(" ".join(raw_tokens))
    if cleaned and _normalize_phrase(cleaned) in DISCOVERY_GENERIC_TOPIC_PHRASES:
        return None
    return cleaned or None


def _is_valid_topic_candidate(value: str) -> bool:
    if any(marker in value for marker in ("\u00c3", "\u00e2", "\ufffd")):
        return False
    if any(marker in value for marker in ("Ã", "â", "�")):
        return False
    normalized = _normalize_phrase(value)
    tokens = normalized.split()
    if not tokens or len(tokens) > 4:
        return False
    if any(char.isdigit() for char in normalized):
        return False
    if any(char in normalized for char in {"&", "+", "(", ")"}):
        return False
    if any(token in DISCOVERY_DYNAMIC_FORMAT_TOKENS for token in tokens):
        return False
    if any(_strip_compound_format_suffix(token) is not None for token in tokens):
        return False
    if any(token in DISCOVERY_NON_BOOK_TOKENS for token in tokens):
        return False
    if has_non_book_markers(normalized):
        return False
    if normalized in DISCOVERY_GENERIC_TOPIC_PHRASES:
        return False
    if len(tokens) >= 3 and "und" in tokens:
        return False
    if tokens[-1] in {"grundlagen", "funktion", "funktionen", "ueberblick", "anlehnung"}:
        return False

    content_tokens = [
        token
        for token in tokens
        if token not in DISCOVERY_DYNAMIC_TOPIC_STOPWORDS and token not in DISCOVERY_DYNAMIC_TOPIC_NOISE
    ]
    if not content_tokens:
        return False
    if all(token in DISCOVERY_GENERIC_TOPIC_TOKENS for token in content_tokens):
        return False
    if len(content_tokens) >= 2:
        for index, token in enumerate(content_tokens):
            for other in content_tokens[index + 1 :]:
                if token.startswith(other) or other.startswith(token):
                    return False
    if len(content_tokens) == 1 and len(content_tokens[0]) < 4 and content_tokens[0] not in {"adhs", "eeg"}:
        return False
    return True


def _collapse_topic_tokens(raw_tokens: list[str]) -> list[str]:
    normalized_tokens = [_normalize_discovery_token(token) for token in raw_tokens]
    normalized_tokens = [token for token in normalized_tokens if token]
    if not normalized_tokens:
        return []

    while normalized_tokens and normalized_tokens[-1] in DISCOVERY_DYNAMIC_FORMAT_TOKENS:
        normalized_tokens.pop()
    if not normalized_tokens:
        return []

    if len(normalized_tokens) > 1:
        stripped_last = _strip_compound_format_suffix(normalized_tokens[-1])
        if stripped_last is not None:
            normalized_tokens.pop()
    elif len(normalized_tokens) == 1:
        stripped_single = _strip_compound_format_suffix(normalized_tokens[0])
        if stripped_single is not None:
            normalized_tokens[0] = stripped_single

    while normalized_tokens and normalized_tokens[0] in DISCOVERY_DYNAMIC_TOPIC_STOPWORDS:
        normalized_tokens.pop(0)
    while normalized_tokens and normalized_tokens[0] in DISCOVERY_DYNAMIC_TOPIC_NOISE:
        normalized_tokens.pop(0)
    return normalized_tokens


def _strip_compound_format_suffix(token: str) -> str | None:
    for suffix in sorted(DISCOVERY_COMPOUND_FORMAT_SUFFIXES, key=len, reverse=True):
        if token == suffix:
            return None
        if token.endswith(suffix):
            stem = token[: -len(suffix)]
            if len(stem) >= 4:
                if stem.endswith("s") and len(stem) >= 6:
                    stem = stem[:-1]
                return stem
    return None


def _normalize_discovery_token(value: str) -> str:
    return _normalize_phrase(value).replace(" ", "")


def _slugify_discovery_value(value: str) -> str:
    return _normalize_phrase(value).replace(" ", "-")[:255]


def _canonical_discovery_slug(value: str) -> str:
    canonical = value.casefold()
    for before, after in (("ae", "a"), ("oe", "o"), ("ue", "u"), ("ss", "s")):
        canonical = canonical.replace(before, after)
    return canonical


def _book_type_hint_from_source_text(value: str) -> str | None:
    normalized = _normalize_phrase(value)
    if any(token in normalized for token in ("handbuch", "ratgeber", "leitfaden", "praxisbuch", "kochbuch", "sammlung")):
        return "sachbuch"
    if any(
        token in normalized
        for token in ("tagebuch", "tracker", "planer", "journal", "logbuch", "ordner", "checklistenbuch", "vorlagenbuch", "notizbuch")
    ):
        return "medium_content"
    return None


def _book_type_hint_from_intent(intent_family: str | None) -> str | None:
    if intent_family in {"ratgeber", "leitfaden", "handbuch", "praxisbuch"}:
        return "sachbuch"
    if intent_family in {"tagebuch", "logbuch", "tracker", "planer", "journal", "arbeitsbuch"}:
        return "medium_content"
    return None


def _generate_candidate_batch(
    db: Session,
    run: DiscoveryRun,
    *,
    limit: int,
) -> GenerationBatch:
    ensure_default_discovery_universe(db)
    topics = _active_rows(db, DiscoveryTopic)
    audiences = _active_rows(db, DiscoveryAudience)
    pain_points = _active_rows(db, DiscoveryPainPoint)
    contexts = _active_rows(db, DiscoveryContext)
    formats = _active_rows(db, DiscoveryBookFormat)

    existing_by_phrase = {
        candidate.normalized_phrase: candidate
        for candidate in db.scalars(select(DiscoveryCandidate))
    }

    generated_specs: dict[str, CandidateSpec] = {}
    ranked_audiences = [None, *audiences[:8]]
    ranked_contexts = [None, *contexts[:7]]
    ranked_pain_points = [None, *pain_points[:6]]

    for topic in topics:
        for book_format in formats:
            for pain_point in ranked_pain_points:
                if not _is_topic_format_pair_supported(topic, book_format, pain_point):
                    continue
                for audience in ranked_audiences:
                    if not _is_topic_audience_pair_supported(topic, audience):
                        continue
                    for context in ranked_contexts:
                        if not _is_topic_context_pair_supported(topic, context):
                            continue
                        phrase = _compose_candidate_phrase(
                            topic.name,
                            audience.name if audience else None,
                            context.name if context else None,
                            pain_point.name if pain_point else None,
                            book_format.name,
                        )
                        if len(phrase) > 255:
                            continue
                        spec = _build_spec(
                            topic=topic,
                            audience=audience,
                            pain_point=pain_point,
                            context=context,
                            book_format=book_format,
                            phrase=phrase,
                        )
                        if spec.generation_score < 44:
                            continue
                        existing = generated_specs.get(spec.normalized_phrase)
                        if existing is None or spec.generation_score > existing.generation_score:
                            generated_specs[spec.normalized_phrase] = spec

    ranked_specs = sorted(
        generated_specs.values(),
        key=lambda spec: (
            spec.generation_score,
            spec.pain_clarity_score,
            100 - _risk_value(spec.risk_level),
            spec.specificity_score,
        ),
        reverse=True,
    )
    selected_specs = _select_ranked_specs(ranked_specs, limit=limit)

    created_count = 0
    updated_count = 0
    candidates: list[DiscoveryCandidate] = []
    for spec in selected_specs:
        existing = existing_by_phrase.get(spec.normalized_phrase)
        if existing is None:
            existing = db.scalars(
                select(DiscoveryCandidate).where(DiscoveryCandidate.normalized_phrase == spec.normalized_phrase)
            ).first()
        if existing is None:
            candidate = DiscoveryCandidate(
                discovery_run_id=run.id,
                topic_id=spec.topic_id,
                audience_id=spec.audience_id,
                pain_point_id=spec.pain_point_id,
                context_id=spec.context_id,
                book_format_id=spec.book_format_id,
                candidate_phrase=spec.candidate_phrase,
                normalized_phrase=spec.normalized_phrase,
                semantic_key=spec.semantic_key,
                semantic_family=spec.semantic_family,
                book_type_hint=spec.book_type_hint,
                risk_level=spec.risk_level,
                status="generated",
                generation_score=spec.generation_score,
                specificity_score=spec.specificity_score,
                intent_score=spec.intent_score,
                audience_clarity_score=spec.audience_clarity_score,
                format_suitability_score=spec.format_suitability_score,
                competition_probability_score=spec.competition_probability_score,
                production_effort_score=spec.production_effort_score,
                pain_clarity_score=spec.pain_clarity_score,
            )
            db.add(candidate)
            db.flush()
            existing_by_phrase[spec.normalized_phrase] = candidate
            candidates.append(candidate)
            created_count += 1
            continue

        existing.discovery_run_id = run.id
        existing.topic_id = spec.topic_id
        existing.audience_id = spec.audience_id
        existing.pain_point_id = spec.pain_point_id
        existing.context_id = spec.context_id
        existing.book_format_id = spec.book_format_id
        existing.semantic_key = spec.semantic_key
        existing.semantic_family = spec.semantic_family
        existing.book_type_hint = spec.book_type_hint
        existing.risk_level = spec.risk_level
        existing.generation_score = spec.generation_score
        existing.specificity_score = spec.specificity_score
        existing.intent_score = spec.intent_score
        existing.audience_clarity_score = spec.audience_clarity_score
        existing.format_suitability_score = spec.format_suitability_score
        existing.competition_probability_score = spec.competition_probability_score
        existing.production_effort_score = spec.production_effort_score
        existing.pain_clarity_score = spec.pain_clarity_score
        if existing.status != "validated":
            existing.status = "generated"
        db.add(existing)
        existing_by_phrase[spec.normalized_phrase] = existing
        candidates.append(existing)
        updated_count += 1

    db.commit()
    for candidate in candidates:
        db.refresh(candidate)

    return GenerationBatch(
        run=run,
        created_count=created_count,
        updated_count=updated_count,
        deduplicated_count=len(generated_specs),
        candidates=candidates,
    )


def _build_spec(
    *,
    topic: DiscoveryTopic,
    audience: DiscoveryAudience | None,
    pain_point: DiscoveryPainPoint | None,
    context: DiscoveryContext | None,
    book_format: DiscoveryBookFormat,
    phrase: str,
) -> CandidateSpec:
    book_type_hint = _merge_book_type_hints(topic.book_type_hint, book_format.book_type_hint)
    intelligence = infer_keyword_intelligence(phrase, book_type=book_type_hint)
    semantic_key, semantic_family = semantic_key_for_candidate_phrase(phrase)
    pain_clarity_score = clamp(
        12
        + (16 if audience else 0)
        + (14 if pain_point else 0)
        + (12 if context else 0)
        + 10
        + intelligence.specificity_score * 0.12
        + intelligence.intent_score * 0.08
    )
    generation_score = clamp(
        pain_clarity_score * 0.22
        + intelligence.specificity_score * 0.16
        + intelligence.intent_score * 0.12
        + intelligence.audience_clarity_score * 0.08
        + intelligence.format_suitability_score * 0.10
        + max(0, 100 - intelligence.competition_probability_score) * 0.10
        + _priority_blend(topic.priority, audience, pain_point, context, book_format) * 0.14
        + max(0, 100 - intelligence.production_effort_score) * 0.08
        + max(0, 100 - _risk_value(_merge_risk_levels(topic.risk_level, intelligence.risk_level))) * 0.10
    )
    normalized_phrase = _normalize_phrase(phrase)
    return CandidateSpec(
        topic_id=topic.id,
        audience_id=audience.id if audience else None,
        pain_point_id=pain_point.id if pain_point else None,
        context_id=context.id if context else None,
        book_format_id=book_format.id,
        candidate_phrase=phrase,
        normalized_phrase=normalized_phrase,
        semantic_key=semantic_key,
        semantic_family=semantic_family,
        book_type_hint=book_type_hint,
        risk_level=_merge_risk_levels(topic.risk_level, intelligence.risk_level),
        generation_score=generation_score,
        specificity_score=intelligence.specificity_score,
        intent_score=intelligence.intent_score,
        audience_clarity_score=intelligence.audience_clarity_score,
        format_suitability_score=intelligence.format_suitability_score,
        competition_probability_score=intelligence.competition_probability_score,
        production_effort_score=intelligence.production_effort_score,
        pain_clarity_score=pain_clarity_score,
    )


def _compose_candidate_phrase(
    topic_name: str,
    audience_name: str | None,
    context_name: str | None,
    pain_point_name: str | None,
    format_name: str,
) -> str:
    if " " in topic_name:
        phrase = f"{topic_name} {format_name}"
    else:
        phrase = f"{topic_name}-{format_name}"

    pain_suffix = _pain_point_suffix(
        pain_point_name,
        format_name=format_name,
        context_name=context_name,
    )
    if pain_suffix:
        phrase += f" {pain_suffix}"
    if audience_name:
        phrase += f" fuer {audience_name}"
    if context_name:
        phrase += f" {context_name}"
    return phrase


def _pain_point_suffix(
    pain_point_name: str | None,
    *,
    format_name: str,
    context_name: str | None,
) -> str | None:
    if pain_point_name is None:
        return None
    if _normalize_phrase(pain_point_name) == "dokumentation":
        return None

    format_slug = _slugify_discovery_value(format_name)
    if format_slug in DISCOVERY_SUFFIX_BLOCKED_FORMATS:
        return None

    suffix = DISCOVERY_PAIN_POINT_SUFFIXES.get(_normalize_phrase(pain_point_name))
    if suffix is None:
        return None
    if context_name and _normalize_phrase(suffix) in _normalize_phrase(context_name):
        return None
    return suffix


def _is_topic_format_pair_supported(
    topic: DiscoveryTopic,
    book_format: DiscoveryBookFormat,
    pain_point: DiscoveryPainPoint | None,
) -> bool:
    if topic.book_type_hint == "medium_content":
        return book_format.book_type_hint == "medium_content"
    if topic.book_type_hint != "sachbuch":
        return True

    if book_format.slug in DISCOVERY_REFERENCE_FORMAT_SLUGS or book_format.book_type_hint == "sachbuch":
        return True

    normalized_topic = _normalize_phrase(topic.name)
    if any(token in normalized_topic for token in DISCOVERY_TRACKING_TOPIC_TOKENS):
        return book_format.slug in DISCOVERY_MEDIUM_CONTENT_FORMAT_SLUGS

    if (
        pain_point is not None
        and pain_point.slug in {"dokumentation", "fehlende-struktur", "alltag-organisieren", "routinen-aufbauen"}
        and book_format.slug in {"arbeitsbuch", "checklistenbuch", "vorlagenbuch", "ordner"}
    ):
        return True

    return False


def _is_topic_audience_pair_supported(
    topic: DiscoveryTopic,
    audience: DiscoveryAudience | None,
) -> bool:
    if audience is None:
        return True
    allowed = TOPIC_ALLOWED_AUDIENCE_SLUGS.get(topic.slug)
    if not allowed:
        if _is_dynamic_topic(topic):
            return False
        return True
    return audience.slug in allowed


def _is_topic_context_pair_supported(
    topic: DiscoveryTopic,
    context: DiscoveryContext | None,
) -> bool:
    if context is None:
        return True
    allowed_topics = CONTEXT_ALLOWED_TOPIC_SLUGS.get(context.slug)
    if not allowed_topics:
        if _is_dynamic_sachbuch_topic(topic):
            return context.slug == "fuer-einsteiger"
        if _is_dynamic_topic(topic):
            return False
        return True
    return topic.slug in allowed_topics


def _is_dynamic_topic(topic: DiscoveryTopic) -> bool:
    default_slugs = {row["slug"] for row in DEFAULT_TOPICS}
    return topic.slug not in default_slugs


def _is_dynamic_sachbuch_topic(topic: DiscoveryTopic) -> bool:
    return _is_dynamic_topic(topic) and topic.book_type_hint == "sachbuch"


def _priority_blend(
    topic_priority: int,
    audience: DiscoveryAudience | None,
    pain_point: DiscoveryPainPoint | None,
    context: DiscoveryContext | None,
    book_format: DiscoveryBookFormat,
) -> int:
    values = [
        topic_priority,
        audience.priority if audience else 72,
        pain_point.priority if pain_point else 70,
        context.priority if context else 68,
        book_format.priority,
    ]
    return clamp(sum(values) / len(values))


def _merge_book_type_hints(topic_hint: str | None, format_hint: str | None) -> str | None:
    return topic_hint or format_hint


def _merge_risk_levels(left: str | None, right: str | None) -> str | None:
    left_value = _risk_value(left)
    right_value = _risk_value(right)
    if left_value >= right_value:
        return left
    return right


def _risk_value(value: str | None) -> int:
    if value == "high":
        return 78
    if value == "medium":
        return 45
    if value == "low":
        return 18
    return 24


def _normalize_phrase(value: str) -> str:
    normalized = (normalize_text(value) or value).casefold()
    normalized = " ".join(normalized.replace("-", " ").split())
    return normalized[:255]


def _create_run(
    db: Session,
    *,
    mode: str,
    requested_generate_limit: int,
    requested_validate_limit: int,
    auto_generate_reports: bool,
    notes: str,
) -> DiscoveryRun:
    run = DiscoveryRun(
        mode=mode,
        status="running",
        requested_generate_limit=requested_generate_limit,
        requested_validate_limit=requested_validate_limit,
        auto_generate_reports=auto_generate_reports,
        notes=notes,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _select_candidates_for_validation(
    db: Session,
    *,
    limit: int,
    force: bool,
) -> list[DiscoveryCandidate]:
    candidates = list(
        db.scalars(
            select(DiscoveryCandidate).order_by(
                DiscoveryCandidate.final_opportunity_score.desc().nullslast(),
                DiscoveryCandidate.generation_score.desc().nullslast(),
                DiscoveryCandidate.updated_at.desc(),
                DiscoveryCandidate.id.asc(),
            )
        )
    )
    pending = [
        candidate
        for candidate in _filter_eligible_candidates(db, candidates)
        if force or not _can_reuse_validation(candidate, force=False)
    ]
    return _select_ranked_candidates(pending, limit=limit)


def _candidate_family_key(candidate: DiscoveryCandidate) -> str:
    return ":".join(
        [
            str(candidate.topic_id),
            str(candidate.audience_id or 0),
            str(candidate.book_format_id or 0),
            str(candidate.context_id or 0),
            str(candidate.pain_point_id or 0),
        ]
    )


def _candidate_spec_family_key(spec: CandidateSpec) -> str:
    return ":".join(
        [
            str(spec.topic_id),
            str(spec.audience_id or 0),
            str(spec.book_format_id or 0),
            str(spec.context_id or 0),
            str(spec.pain_point_id or 0),
        ]
    )


def _candidate_spec_topic_format_key(spec: CandidateSpec) -> str:
    return ":".join([str(spec.topic_id), str(spec.book_format_id or 0)])


def _candidate_topic_format_key(candidate: DiscoveryCandidate) -> str:
    return ":".join([str(candidate.topic_id), str(candidate.book_format_id or 0)])


def _topic_selection_cap(limit: int) -> int:
    if limit <= 24:
        return 1
    if limit <= 72:
        return 2
    return 3


def _select_ranked_specs(specs: list[CandidateSpec], *, limit: int) -> list[CandidateSpec]:
    if limit <= 0:
        return []

    selected: list[CandidateSpec] = []
    seen_families: set[str] = set()
    selected_phrases: set[str] = set()
    selected_semantic_families: set[str] = set()
    topic_counts: Counter[int] = Counter()
    topic_format_counts: Counter[str] = Counter()

    unique_topic_frontier: list[CandidateSpec] = []
    seen_topics: set[int] = set()
    for spec in specs:
        if spec.topic_id in seen_topics:
            continue
        unique_topic_frontier.append(spec)
        seen_topics.add(spec.topic_id)

    for pool, topic_cap in ((unique_topic_frontier, 1), (specs, _topic_selection_cap(limit))):
        for spec in pool:
            if _append_spec_if_distinct(
                spec,
                selected=selected,
                seen_families=seen_families,
                selected_phrases=selected_phrases,
                selected_semantic_families=selected_semantic_families,
                topic_counts=topic_counts,
                topic_format_counts=topic_format_counts,
                topic_cap=topic_cap,
            ):
                if len(selected) >= limit:
                    return selected
    return selected


def _append_spec_if_distinct(
    spec: CandidateSpec,
    *,
    selected: list[CandidateSpec],
    seen_families: set[str],
    selected_phrases: set[str],
    selected_semantic_families: set[str],
    topic_counts: Counter[int],
    topic_format_counts: Counter[str],
    topic_cap: int,
) -> bool:
    if spec.normalized_phrase in selected_phrases:
        return False

    family_key = _candidate_spec_family_key(spec)
    if family_key in seen_families:
        return False

    topic_format_key = _candidate_spec_topic_format_key(spec)
    if topic_counts[spec.topic_id] >= topic_cap:
        return False
    if topic_format_counts[topic_format_key] >= 1:
        return False
    if spec.semantic_family and spec.semantic_family in selected_semantic_families:
        return False
    if _is_spec_semantic_duplicate(spec, selected):
        return False

    selected.append(spec)
    selected_phrases.add(spec.normalized_phrase)
    seen_families.add(family_key)
    topic_counts[spec.topic_id] += 1
    topic_format_counts[topic_format_key] += 1
    if spec.semantic_family:
        selected_semantic_families.add(spec.semantic_family)
    return True


def _is_spec_semantic_duplicate(spec: CandidateSpec, selected: list[CandidateSpec]) -> bool:
    for existing in selected:
        if spec.semantic_key and existing.semantic_key and spec.semantic_key == existing.semantic_key:
            return True
        similarity = semantic_text_similarity(spec.candidate_phrase, existing.candidate_phrase)
        if similarity >= 0.88:
            return True
    return False


def _select_ranked_candidates(
    candidates: list[DiscoveryCandidate],
    *,
    limit: int,
) -> list[DiscoveryCandidate]:
    if limit <= 0:
        return []

    selected: list[DiscoveryCandidate] = []
    seen_candidate_ids: set[int] = set()
    seen_families: set[str] = set()
    selected_semantic_families: set[str] = set()
    topic_counts: Counter[int] = Counter()
    topic_format_counts: Counter[str] = Counter()

    unique_topic_frontier: list[DiscoveryCandidate] = []
    seen_topics: set[int] = set()
    for candidate in candidates:
        if candidate.topic_id in seen_topics:
            continue
        unique_topic_frontier.append(candidate)
        seen_topics.add(candidate.topic_id)

    for pool, topic_cap in ((unique_topic_frontier, 1), (candidates, _topic_selection_cap(limit))):
        for candidate in pool:
            if _append_candidate_if_distinct(
                candidate,
                selected=selected,
                seen_candidate_ids=seen_candidate_ids,
                seen_families=seen_families,
                selected_semantic_families=selected_semantic_families,
                topic_counts=topic_counts,
                topic_format_counts=topic_format_counts,
                topic_cap=topic_cap,
            ):
                if len(selected) >= limit:
                    return selected
    return selected


def _append_candidate_if_distinct(
    candidate: DiscoveryCandidate,
    *,
    selected: list[DiscoveryCandidate],
    seen_candidate_ids: set[int],
    seen_families: set[str],
    selected_semantic_families: set[str],
    topic_counts: Counter[int],
    topic_format_counts: Counter[str],
    topic_cap: int,
) -> bool:
    if candidate.id in seen_candidate_ids:
        return False

    family_key = _candidate_family_key(candidate)
    if family_key in seen_families:
        return False

    topic_format_key = _candidate_topic_format_key(candidate)
    if topic_counts[candidate.topic_id] >= topic_cap:
        return False
    if topic_format_counts[topic_format_key] >= 1:
        return False
    if candidate.semantic_family and candidate.semantic_family in selected_semantic_families:
        return False
    if _is_candidate_semantic_duplicate(candidate, selected):
        return False

    selected.append(candidate)
    seen_candidate_ids.add(candidate.id)
    seen_families.add(family_key)
    topic_counts[candidate.topic_id] += 1
    topic_format_counts[topic_format_key] += 1
    if candidate.semantic_family:
        selected_semantic_families.add(candidate.semantic_family)
    return True


def _is_candidate_semantic_duplicate(candidate: DiscoveryCandidate, selected: list[DiscoveryCandidate]) -> bool:
    for existing in selected:
        if candidate.semantic_key and existing.semantic_key and candidate.semantic_key == existing.semantic_key:
            return True
        similarity = semantic_text_similarity(candidate.candidate_phrase, existing.candidate_phrase)
        if similarity >= 0.88:
            return True
    return False


def _can_reuse_validation(candidate: DiscoveryCandidate, *, force: bool) -> bool:
    if force or candidate.status != "validated" or candidate.last_validated_at is None:
        return False
    last_validated_at = candidate.last_validated_at
    if last_validated_at.tzinfo is None:
        last_validated_at = last_validated_at.replace(tzinfo=UTC)
    return datetime.now(UTC) - last_validated_at < timedelta(hours=RECENT_VALIDATION_REUSE_HOURS)


def _validate_candidate(
    db: Session,
    candidate: DiscoveryCandidate,
    *,
    run: DiscoveryRun,
    auto_generate_reports: bool,
) -> None:
    declared_audience = _candidate_block_name(db, DiscoveryAudience, candidate.audience_id)
    declared_pain_point = _candidate_block_name(db, DiscoveryPainPoint, candidate.pain_point_id)
    declared_book_format = _candidate_block_name(db, DiscoveryBookFormat, candidate.book_format_id)
    _refresh_candidate_generation_metrics(db, candidate)
    candidate.discovery_run_id = run.id
    candidate.status = "validating"
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    seed_keyword = _get_or_create_seed_keyword(db, candidate)
    pipeline = run_seed_pipeline(
        db,
        seed_keyword,
        collect_related_limit=3,
        enrich_top_books=6,
        review_page=1,
        reuse_existing_runs=True,
    )
    cluster_analysis = pipeline.cluster_analysis or build_and_analyze_seed_cluster(db, seed_keyword)

    sachbuch_analysis: SachbuchAnalysisRead | None = None
    if cluster_analysis.recommended_book_class == "sachbuch" or candidate.book_type_hint == "sachbuch":
        try:
            sachbuch_analysis = analyze_sachbuch_cluster(db, cluster_analysis.niche_cluster_id)
        except ValueError:
            sachbuch_analysis = None

    reports_generated = _generate_reports_for_candidate(
        db,
        cluster_analysis,
        sachbuch_analysis,
        auto_generate_reports=auto_generate_reports,
    )
    review_counts = [
        book.latest_review_count
        for book in cluster_analysis.competitor_books[:10]
        if book.latest_review_count is not None
    ]
    demand_score = cluster_analysis.score.demand_score or 0
    competition_score = clamp(
        (cluster_analysis.score.entry_feasibility_score or 0) * 0.56
        + (cluster_analysis.score.new_entrant_signal or 0) * 0.18
        + max(0, 100 - (cluster_analysis.score.saturation_risk or 0)) * 0.16
        + max(0, 100 - (cluster_analysis.score.review_wall_risk or 0)) * 0.10
    )
    pain_clarity_score = clamp(
        (candidate.pain_clarity_score or 0) * 0.55
        + (candidate.specificity_score or 0) * 0.15
        + (candidate.intent_score or 0) * 0.12
        + (candidate.audience_clarity_score or 0) * 0.10
        + (candidate.format_suitability_score or 0) * 0.08
    )
    gap_score = _gap_score(cluster_analysis, sachbuch_analysis)
    production_difficulty_score = clamp(
        (cluster_analysis.score.research_effort_score or 0) * 0.72
        + (candidate.production_effort_score or 0) * 0.28
    )
    risk_score = _risk_score(cluster_analysis, sachbuch_analysis, candidate)
    strategic_score = (
        sachbuch_analysis.sachbuch_score.final_score
        if sachbuch_analysis and sachbuch_analysis.sachbuch_score.final_score is not None
        else cluster_analysis.score.final_score or 0
    )
    final_opportunity_score = clamp(
        (cluster_analysis.score.final_score or 0) * 0.40
        + strategic_score * 0.16
        + demand_score * 0.14
        + competition_score * 0.11
        + pain_clarity_score * 0.10
        + gap_score * 0.13
        - production_difficulty_score * 0.05
        - risk_score * 0.11
        + 10
    )
    decision = _decision_for_candidate(final_opportunity_score, demand_score, competition_score, risk_score)
    go_reasons, no_go_reasons = _decision_reasons(
        cluster_analysis,
        sachbuch_analysis,
        demand_score=demand_score,
        competition_score=competition_score,
        pain_clarity_score=pain_clarity_score,
        gap_score=gap_score,
        risk_score=risk_score,
    )

    candidate.keyword_id = seed_keyword.id
    candidate.niche_cluster_id = cluster_analysis.niche_cluster_id
    candidate.validated_book_type = cluster_analysis.recommended_book_class
    candidate.validated_target_audience = (
        sachbuch_analysis.recommended_target_audience
        if sachbuch_analysis
        else (
            declared_audience
            or seed_keyword.target_audience
            or (
                cluster_analysis.audience_hints[0]
                if cluster_analysis.audience_hints
                and len(cluster_analysis.audience_hints[0]) <= 90
                else None
            )
        )
    )
    candidate.status = "validated"
    candidate.demand_score = demand_score
    candidate.competition_score = competition_score
    candidate.pain_clarity_score = pain_clarity_score
    candidate.gap_score = gap_score
    candidate.production_difficulty_score = production_difficulty_score
    candidate.risk_score = risk_score
    candidate.final_opportunity_score = final_opportunity_score
    candidate.decision = decision
    candidate.relevant_book_count = cluster_analysis.book_count
    candidate.related_keyword_count = cluster_analysis.keyword_count
    candidate.top_competitor_review_median = int(median(review_counts)) if review_counts else None
    candidate.bsr_coverage = cluster_analysis.competitor_summary.bsr_snapshot_coverage
    candidate.report_count = reports_generated
    candidate.market_summary = _market_summary(cluster_analysis)
    candidate.gap_summary = _gap_summary(cluster_analysis, sachbuch_analysis)
    candidate.reason_summary = _reason_summary(decision, go_reasons, no_go_reasons)
    candidate.recommended_angle = _recommended_angle(
        cluster_analysis,
        sachbuch_analysis,
        declared_audience=declared_audience,
        declared_pain_point=declared_pain_point,
        declared_book_format=declared_book_format,
    )
    candidate.validation_notes = (
        f"Cluster {cluster_analysis.niche_cluster_name} validated from discovery candidate "
        f"with {cluster_analysis.keyword_count} related keywords."
    )
    candidate.last_validated_at = datetime.now(UTC)

    run.validated_count += 1
    run.kept_count += 1 if decision == "GO" else 0
    db.add(candidate)
    db.add(run)
    db.commit()


def _get_or_create_seed_keyword(db: Session, candidate: DiscoveryCandidate) -> Keyword:
    keyword = db.get(Keyword, candidate.keyword_id) if candidate.keyword_id else None
    if keyword is None:
        keyword = db.scalars(
            select(Keyword).where(
                Keyword.keyword == candidate.candidate_phrase,
                Keyword.marketplace == candidate.marketplace,
                Keyword.language == candidate.language,
                Keyword.seed_keyword_id == None,  # noqa: E711
            )
        ).first()

    intelligence = infer_keyword_intelligence(
        candidate.candidate_phrase,
        book_type=candidate.book_type_hint,
    )
    if keyword is None:
        keyword = Keyword(
            keyword=candidate.candidate_phrase,
            language=candidate.language,
            marketplace=candidate.marketplace,
            keyword_type="discovered",
            target_audience=candidate.validated_target_audience or intelligence.target_audience,
            category_hint=intelligence.category_hint,
            search_intent_family=intelligence.search_intent_family,
            specificity_score=intelligence.specificity_score,
            intent_score=intelligence.intent_score,
            audience_clarity_score=intelligence.audience_clarity_score,
            format_suitability_score=intelligence.format_suitability_score,
            competition_probability_score=intelligence.competition_probability_score,
            production_effort_score=intelligence.production_effort_score,
            status="discovered",
            book_type=candidate.book_type_hint,
            risk_level=candidate.risk_level or intelligence.risk_level,
            priority=min(100, candidate.generation_score or 60),
            notes=f"Auto-created from discovery candidate {candidate.id}.",
        )
        db.add(keyword)
        db.commit()
        db.refresh(keyword)
        return keyword

    keyword.keyword_type = keyword.keyword_type or "discovered"
    keyword.target_audience = keyword.target_audience or intelligence.target_audience
    keyword.category_hint = keyword.category_hint or intelligence.category_hint
    keyword.search_intent_family = keyword.search_intent_family or intelligence.search_intent_family
    keyword.specificity_score = keyword.specificity_score or intelligence.specificity_score
    keyword.intent_score = keyword.intent_score or intelligence.intent_score
    keyword.audience_clarity_score = keyword.audience_clarity_score or intelligence.audience_clarity_score
    keyword.format_suitability_score = keyword.format_suitability_score or intelligence.format_suitability_score
    keyword.competition_probability_score = keyword.competition_probability_score or intelligence.competition_probability_score
    keyword.production_effort_score = keyword.production_effort_score or intelligence.production_effort_score
    keyword.status = keyword.status or "discovered"
    keyword.book_type = keyword.book_type or candidate.book_type_hint
    keyword.risk_level = keyword.risk_level or candidate.risk_level or intelligence.risk_level
    keyword.priority = max(keyword.priority, min(100, candidate.generation_score or 0))
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


def _generate_reports_for_candidate(
    db: Session,
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
    *,
    auto_generate_reports: bool,
) -> int:
    if not auto_generate_reports:
        return _report_count(db, cluster_analysis.niche_cluster_id)

    report_types = ["go_no_go_report", "competitor_report"]
    if sachbuch_analysis is not None:
        report_types.append("book_concept_report")
        report_types.append("sachbuch_opportunity_report")
    else:
        report_types.append("keyword_report")

    for report_type in report_types:
        generate_cluster_report(db, cluster_analysis.niche_cluster_id, report_type=report_type)
    return _report_count(db, cluster_analysis.niche_cluster_id)


def _report_count(db: Session, cluster_id: int) -> int:
    return int(
        db.scalar(
            select(func.count(func.distinct(Report.report_type))).where(Report.niche_cluster_id == cluster_id)
        )
        or 0
    )


def _gap_score(
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
) -> int:
    if sachbuch_analysis is None:
        return clamp(
            (cluster_analysis.score.differentiation_score or 0) * 0.70
            + (cluster_analysis.score.review_insight_score or 0) * 0.30
        )
    topic_gap_signal = clamp(
        (
            (sachbuch_analysis.topic_gap.missing_examples_signal or 0)
            + (sachbuch_analysis.topic_gap.missing_checklists_signal or 0)
            + (sachbuch_analysis.topic_gap.localization_gap_signal or 0)
        )
        / 3
    )
    return clamp(
        (cluster_analysis.score.differentiation_score or 0) * 0.42
        + (sachbuch_analysis.sachbuch_score.topic_gap_signal or 0) * 0.28
        + topic_gap_signal * 0.30
    )


def _risk_score(
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
    candidate: DiscoveryCandidate,
) -> int:
    values = [
        cluster_analysis.score.compliance_risk or 0,
        cluster_analysis.score.authority_risk or 0,
        cluster_analysis.score.content_complexity_risk or 0,
        _risk_value(candidate.risk_level),
    ]
    if sachbuch_analysis is not None:
        values.extend(
            [
                sachbuch_analysis.sachbuch_score.liability_risk or 0,
                sachbuch_analysis.sachbuch_score.update_risk or 0,
            ]
        )
    return max(values)


def _decision_for_candidate(
    final_opportunity_score: int,
    demand_score: int,
    competition_score: int,
    risk_score: int,
) -> str:
    if final_opportunity_score >= 70 and demand_score >= 55 and competition_score >= 45 and risk_score < 72:
        return "GO"
    if final_opportunity_score >= 48 and risk_score < 82:
        return "MAYBE"
    return "NO-GO"


def _decision_reasons(
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
    *,
    demand_score: int,
    competition_score: int,
    pain_clarity_score: int,
    gap_score: int,
    risk_score: int,
) -> tuple[list[str], list[str]]:
    go_reasons: list[str] = []
    no_go_reasons: list[str] = []

    if demand_score >= 60:
        go_reasons.append("demand exists across the visible Amazon result set")
    else:
        no_go_reasons.append("demand signals stay too weak or too shallow")

    if competition_score >= 55:
        go_reasons.append("competition looks beatable rather than locked by a review wall")
    else:
        no_go_reasons.append("the visible competitor set still looks hard to dislodge")

    if pain_clarity_score >= 70:
        go_reasons.append("audience, problem, context and format are specific enough to position clearly")
    else:
        no_go_reasons.append("the idea is still not specific enough in audience/problem/format terms")

    if gap_score >= 60:
        go_reasons.append("review complaints and competitor gaps point to a clearer product angle")
    else:
        no_go_reasons.append("the market gap is still too thin or too generic")

    if risk_score >= 70:
        no_go_reasons.append("risk and authority burden are too elevated for a fast, clean opportunity")
    else:
        go_reasons.append("risk remains manageable relative to the opportunity")

    if sachbuch_analysis and (sachbuch_analysis.topic_gap.localization_gap_signal or 0) >= 35:
        go_reasons.append("German-specific localization is visibly under-served")

    if cluster_analysis.competitor_summary.average_review_count >= 250:
        no_go_reasons.append("average visible review counts are already heavy")

    return go_reasons[:5], no_go_reasons[:5]


def _market_summary(cluster_analysis: NicheClusterAnalysisRead) -> str:
    return (
        f"{cluster_analysis.book_count} visible books across {cluster_analysis.keyword_count} related keywords. "
        f"Average visible review count is {cluster_analysis.competitor_summary.average_review_count:.1f} "
        f"with BSR coverage {cluster_analysis.competitor_summary.bsr_snapshot_coverage}%."
    )


def _gap_summary(
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
) -> str:
    if sachbuch_analysis is not None and sachbuch_analysis.topic_gap.topic_gap_summary:
        return sachbuch_analysis.topic_gap.topic_gap_summary
    lines = cluster_analysis.top_opportunities[:2] + cluster_analysis.missing_features[:2]
    if not lines:
        return "No strong competitor gap was persisted yet."
    return " ".join(lines)


def _reason_summary(decision: str, go_reasons: list[str], no_go_reasons: list[str]) -> str:
    reasons = go_reasons if decision == "GO" else no_go_reasons or go_reasons
    if not reasons:
        return decision
    joined = "\n".join(f"- {reason}" for reason in reasons)
    return f"{decision}\n{joined}"


def _recommended_angle(
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
    *,
    declared_audience: str | None,
    declared_pain_point: str | None,
    declared_book_format: str | None,
) -> str | None:
    if sachbuch_analysis is not None:
        return sachbuch_analysis.reader_promise
    if cluster_analysis.top_opportunities:
        return cluster_analysis.top_opportunities[0]
    if cluster_analysis.missing_features:
        return cluster_analysis.missing_features[0]
    if declared_book_format and (declared_audience or declared_pain_point):
        parts = [declared_book_format]
        if declared_audience:
            parts.append(f"fuer {declared_audience}")
        if declared_pain_point:
            parts.append(f"mit Fokus auf {declared_pain_point}")
        return " ".join(parts)
    return None


def _candidate_block_name(
    db: Session,
    model: type[object],
    record_id: int | None,
) -> str | None:
    if record_id is None:
        return None
    record = db.get(model, record_id)
    if record is None:
        return None
    return record.name


def _refresh_candidate_generation_metrics(db: Session, candidate: DiscoveryCandidate) -> None:
    topic = db.get(DiscoveryTopic, candidate.topic_id)
    book_format = db.get(DiscoveryBookFormat, candidate.book_format_id) if candidate.book_format_id else None
    if topic is None or book_format is None:
        return

    audience = db.get(DiscoveryAudience, candidate.audience_id) if candidate.audience_id else None
    pain_point = db.get(DiscoveryPainPoint, candidate.pain_point_id) if candidate.pain_point_id else None
    context = db.get(DiscoveryContext, candidate.context_id) if candidate.context_id else None
    spec = _build_spec(
        topic=topic,
        audience=audience,
        pain_point=pain_point,
        context=context,
        book_format=book_format,
        phrase=candidate.candidate_phrase,
    )
    candidate.book_type_hint = spec.book_type_hint
    candidate.semantic_key = spec.semantic_key
    candidate.semantic_family = spec.semantic_family
    candidate.risk_level = spec.risk_level
    candidate.generation_score = spec.generation_score
    candidate.specificity_score = spec.specificity_score
    candidate.intent_score = spec.intent_score
    candidate.audience_clarity_score = spec.audience_clarity_score
    candidate.format_suitability_score = spec.format_suitability_score
    candidate.competition_probability_score = spec.competition_probability_score
    candidate.production_effort_score = spec.production_effort_score
    candidate.pain_clarity_score = spec.pain_clarity_score


def _serialize_candidates(
    db: Session,
    candidates: list[DiscoveryCandidate],
) -> list[DiscoveryCandidateRead]:
    if not candidates:
        return []

    topic_map = {item.id: item.name for item in db.scalars(select(DiscoveryTopic))}
    audience_map = {item.id: item.name for item in db.scalars(select(DiscoveryAudience))}
    pain_map = {item.id: item.name for item in db.scalars(select(DiscoveryPainPoint))}
    context_map = {item.id: item.name for item in db.scalars(select(DiscoveryContext))}
    format_map = {item.id: item.name for item in db.scalars(select(DiscoveryBookFormat))}

    return [
        DiscoveryCandidateRead(
            id=candidate.id,
            topic=topic_map.get(candidate.topic_id, "Unknown"),
            audience=audience_map.get(candidate.audience_id) if candidate.audience_id else None,
            pain_point=pain_map.get(candidate.pain_point_id) if candidate.pain_point_id else None,
            context=context_map.get(candidate.context_id) if candidate.context_id else None,
            book_format=format_map.get(candidate.book_format_id) if candidate.book_format_id else None,
            candidate_phrase=candidate.candidate_phrase,
            semantic_key=candidate.semantic_key,
            semantic_family=candidate.semantic_family,
            language=candidate.language,
            marketplace=candidate.marketplace,
            book_type_hint=candidate.book_type_hint,
            validated_book_type=candidate.validated_book_type,
            risk_level=candidate.risk_level,
            status=candidate.status,
            generation_score=candidate.generation_score,
            specificity_score=candidate.specificity_score,
            intent_score=candidate.intent_score,
            audience_clarity_score=candidate.audience_clarity_score,
            format_suitability_score=candidate.format_suitability_score,
            competition_probability_score=candidate.competition_probability_score,
            production_effort_score=candidate.production_effort_score,
            pain_clarity_score=candidate.pain_clarity_score,
            validated_target_audience=candidate.validated_target_audience,
            demand_score=candidate.demand_score,
            competition_score=candidate.competition_score,
            gap_score=candidate.gap_score,
            production_difficulty_score=candidate.production_difficulty_score,
            risk_score=candidate.risk_score,
            final_opportunity_score=candidate.final_opportunity_score,
            decision=candidate.decision,
            keyword_id=candidate.keyword_id,
            niche_cluster_id=candidate.niche_cluster_id,
            relevant_book_count=candidate.relevant_book_count,
            related_keyword_count=candidate.related_keyword_count,
            top_competitor_review_median=candidate.top_competitor_review_median,
            bsr_coverage=candidate.bsr_coverage,
            report_count=candidate.report_count,
            market_summary=candidate.market_summary,
            gap_summary=candidate.gap_summary,
            reason_summary=candidate.reason_summary,
            recommended_angle=candidate.recommended_angle,
            validation_notes=candidate.validation_notes,
            signals=build_candidate_signals(candidate),
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
            last_validated_at=candidate.last_validated_at,
        )
        for candidate in candidates
    ]


def _serialize_universe_items(items: list[object]) -> list[DiscoveryUniverseItemRead]:
    payload: list[DiscoveryUniverseItemRead] = []
    for item in items:
        payload.append(
            DiscoveryUniverseItemRead(
                id=item.id,
                name=item.name,
                slug=item.slug,
                description=getattr(item, "description", None),
                priority=item.priority,
                active=item.active,
                category_hint=getattr(item, "category_hint", None),
                book_type_hint=getattr(item, "book_type_hint", None),
                risk_level=getattr(item, "risk_level", None),
            )
        )
    return payload
