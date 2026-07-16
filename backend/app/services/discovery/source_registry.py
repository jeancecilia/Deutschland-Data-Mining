"""
Source Registry — manages discovery_sources and seed CSV imports.

Provides:
  - Default source creation
  - CSV-seed-universe import into raw_discovery_items
  - Active-source listing
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import DiscoverySource, RawDiscoveryItem

# Path to the seed universe CSV files (project-relative from backend/)
SEED_UNIVERSE_DIR = Path(__file__).resolve().parents[4] / "data" / "discovery_seed_universes"

SEED_UNIVERSE_MANIFEST: list[dict[str, str]] = [
    # Legacy root-level files
    {"filename": "professions_de.csv", "source_type": "profession_list", "source_name": "Berufsliste DE"},
    {"filename": "exams_de.csv", "source_type": "exam_list", "source_name": "Prüfungen DE"},
    {"filename": "life_events_de.csv", "source_type": "life_event_list", "source_name": "Lebensereignisse DE"},
    {"filename": "hobbies_de.csv", "source_type": "hobby_list", "source_name": "Hobbys & Haustiere DE"},
    {"filename": "family_topics_de.csv", "source_type": "public_list", "source_name": "Familienthemen DE"},
    {"filename": "senior_topics_de.csv", "source_type": "public_list", "source_name": "Seniorenthemen DE"},
    {"filename": "business_topics_de.csv", "source_type": "public_list", "source_name": "Selbstständigkeit DE"},
    {"filename": "ai_use_cases_de.csv", "source_type": "public_list", "source_name": "KI-Anwendungsfälle DE"},
    # New subdirectory files — each gets its own source_type
    {"filename": "audiences/audiences_general_de.csv", "source_type": "audience_list", "source_name": "Zielgruppen Allgemein"},
    {"filename": "audiences/audiences_senior_de.csv", "source_type": "audience_list", "source_name": "Zielgruppen Senioren"},
    {"filename": "audiences/audiences_family_de.csv", "source_type": "audience_list", "source_name": "Zielgruppen Familie"},
    {"filename": "audiences/audiences_business_de.csv", "source_type": "audience_list", "source_name": "Zielgruppen Business"},
    {"filename": "audiences/audiences_learning_de.csv", "source_type": "audience_list", "source_name": "Zielgruppen Lernen"},
    {"filename": "professions/professions_health_de.csv", "source_type": "profession_list", "source_name": "Gesundheitsberufe"},
    {"filename": "professions/professions_craft_de.csv", "source_type": "profession_list", "source_name": "Handwerksberufe"},
    {"filename": "professions/professions_office_de.csv", "source_type": "profession_list", "source_name": "Büroberufe"},
    {"filename": "professions/professions_service_de.csv", "source_type": "profession_list", "source_name": "Dienstleistungsberufe"},
    {"filename": "professions/professions_education_de.csv", "source_type": "profession_list", "source_name": "Bildungsberufe"},
    {"filename": "exams/exams_school_de.csv", "source_type": "exam_list", "source_name": "Schulabschlüsse"},
    {"filename": "exams/exams_vocational_de.csv", "source_type": "exam_list", "source_name": "Berufsprüfungen"},
    {"filename": "exams/exams_language_de.csv", "source_type": "exam_list", "source_name": "Sprachprüfungen"},
    {"filename": "exams/exams_licenses_de.csv", "source_type": "exam_list", "source_name": "Lizenzen"},
    {"filename": "problems/problems_organization_de.csv", "source_type": "problem_list", "source_name": "Organisationsprobleme"},
    {"filename": "problems/problems_learning_de.csv", "source_type": "problem_list", "source_name": "Lernprobleme"},
    {"filename": "problems/problems_health_de.csv", "source_type": "problem_list", "source_name": "Gesundheitsprobleme"},
    {"filename": "problems/problems_work_de.csv", "source_type": "problem_list", "source_name": "Arbeitsprobleme"},
    {"filename": "problems/problems_pets_de.csv", "source_type": "problem_list", "source_name": "Haustierprobleme"},
    {"filename": "health_trackers/health_trackers_de.csv", "source_type": "public_list", "source_name": "Gesundheitstracker"},
    {"filename": "business/business_basics_de.csv", "source_type": "public_list", "source_name": "Business Basics"},
    {"filename": "business/business_admin_de.csv", "source_type": "public_list", "source_name": "Business Admin"},
    {"filename": "ai_use_cases/ai_professions_de.csv", "source_type": "public_list", "source_name": "KI Berufe"},
    {"filename": "household/household_organization_de.csv", "source_type": "public_list", "source_name": "Haushaltsorganisation"},
    {"filename": "pets/pets_dogs_de.csv", "source_type": "hobby_list", "source_name": "Hunde"},
    {"filename": "pets/pets_cats_de.csv", "source_type": "hobby_list", "source_name": "Katzen"},
    {"filename": "hobbies/hobbies_creative_de.csv", "source_type": "hobby_list", "source_name": "Kreative Hobbys"},
    {"filename": "hobbies/hobbies_food_de.csv", "source_type": "hobby_list", "source_name": "Essen & Trinken"},
    {"filename": "hobbies/hobbies_outdoor_de.csv", "source_type": "hobby_list", "source_name": "Outdoor & Sport"},
    {"filename": "hobbies/hobbies_garden_de.csv", "source_type": "hobby_list", "source_name": "Garten"},
    {"filename": "learning/learning_topics_de.csv", "source_type": "public_list", "source_name": "Lernthemen"},
    {"filename": "seniors/senior_topics_de.csv", "source_type": "public_list", "source_name": "Seniorenthemen DE"},
    {"filename": "family/family_topics_de.csv", "source_type": "public_list", "source_name": "Familienthemen DE"},
    {"filename": "formats/book_formats_de.csv", "source_type": "public_list", "source_name": "Buchformate"},
    {"filename": "contexts/contexts_de.csv", "source_type": "public_list", "source_name": "Kontexte"},
]

DEFAULT_SOURCES: list[dict[str, object]] = [
    {
        "name": "Berufsliste Deutschland",
        "source_type": "profession_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "Ausbildungsberufe Deutschland",
        "source_type": "profession_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "IHK-Prüfungen und Abschlüsse",
        "source_type": "exam_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "Lebensereignisse Deutschland",
        "source_type": "life_event_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "Hobbys und Haustiere",
        "source_type": "hobby_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "Familienthemen",
        "source_type": "public_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "Seniorenthemen",
        "source_type": "public_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "Selbstständigkeit & Business",
        "source_type": "public_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "KI-Anwendungsfälle",
        "source_type": "public_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "Gesundheitsnahe Alltagsthemen",
        "source_type": "public_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "Lernen, Schule & Prüfung",
        "source_type": "public_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
    {
        "name": "Organisation & Produktivität",
        "source_type": "public_list",
        "language": "de",
        "country": "DE",
        "is_active": True,
    },
]


def ensure_default_discovery_sources(db: Session) -> list[DiscoverySource]:
    """Create default discovery sources if they don't exist."""
    existing_names = {
        source.name
        for source in db.scalars(select(DiscoverySource))
    }
    created: list[DiscoverySource] = []
    for entry in DEFAULT_SOURCES:
        if entry["name"] not in existing_names:
            source = DiscoverySource(**entry)
            db.add(source)
            created.append(source)
    if created:
        db.commit()
        for source in created:
            db.refresh(source)
    return created


def get_active_discovery_sources(db: Session) -> list[DiscoverySource]:
    """Return all active discovery sources."""
    return list(
        db.scalars(
            select(DiscoverySource)
            .where(DiscoverySource.is_active == True)  # noqa: E712
            .order_by(DiscoverySource.name)
        )
    )


def list_discovery_sources(db: Session) -> list[DiscoverySource]:
    """Return all discovery sources."""
    return list(
        db.scalars(
            select(DiscoverySource).order_by(DiscoverySource.name)
        )
    )


def get_discovery_source_by_type(db: Session, source_type: str) -> DiscoverySource | None:
    """Get the first active source of a given type."""
    return db.scalars(
        select(DiscoverySource)
        .where(
            DiscoverySource.source_type == source_type,
            DiscoverySource.is_active == True,  # noqa: E712
        )
    ).first()


def import_seed_csv_to_raw_items(
    db: Session,
    csv_path: Path,
    source: DiscoverySource,
    *,
    entity_type_override: str | None = None,
    min_priority: int = 0,
    batch_size: int = 5000,
) -> int:
    """Import a seed CSV file into raw_discovery_items using batched inserts.

    CSV format: name,entity_type,priority

    Returns the number of imported items.
    """
    if not csv_path.exists():
        return 0

    now = datetime.now(UTC)

    # ── Load existing raw_text for this source once (in-memory dedup) ──
    existing_texts: set[str] = {
        row[0] for row in db.execute(
            select(RawDiscoveryItem.raw_text).where(
                RawDiscoveryItem.discovery_source_id == source.id
            )
        ).fetchall()
    }

    with open(csv_path, encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        batch: list[RawDiscoveryItem] = []
        imported = 0

        def _flush():
            nonlocal imported
            if not batch:
                return
            db.add_all(batch)
            db.flush()
            imported += len(batch)
            batch.clear()

        for row in reader:
            name = (row.get("name") or "").strip()
            entity_type = (row.get("entity_type") or entity_type_override or "").strip()
            priority_raw = row.get("priority", "50")
            if not name:
                continue
            try:
                priority = int(priority_raw)
            except (ValueError, TypeError):
                priority = 50
            if priority < min_priority:
                continue

            # In-memory dedup
            if name in existing_texts:
                continue
            existing_texts.add(name)

            # Preserve CSV metadata (domain, subdomain, audience, etc.)
            meta: dict[str, object] = {}
            for key, value in row.items():
                stripped = str(value).strip() if value else ""
                if key in ("name", "entity_type", "priority") or not stripped:
                    continue
                meta[key] = stripped
            if entity_type:
                meta["entity_type_hint"] = entity_type
            meta["priority"] = priority

            item = RawDiscoveryItem(
                discovery_source_id=source.id,
                raw_text=name,
                language=source.language,
                country=source.country,
                confidence=max(50, min(100, priority)),
                metadata_json=meta if meta else None,
                status="new",
                collected_at=now,
            )
            batch.append(item)

            if len(batch) >= batch_size:
                _flush()

        _flush()  # final batch

    if imported:
        db.commit()

    return imported


def import_all_seed_universes(db: Session) -> dict[str, int]:
    """Import all CSV seed universes into raw_discovery_items.

    Returns a dict of filename → imported count.
    """
    ensure_default_discovery_sources(db)
    results: dict[str, int] = {}

    for entry in SEED_UNIVERSE_MANIFEST:
        csv_path = SEED_UNIVERSE_DIR / entry["filename"]
        # Resolve by exact source name first (one source per manifest entry)
        source = db.scalars(
            select(DiscoverySource).where(DiscoverySource.name == entry["source_name"])
        ).first()
        if source is None:
            source = get_discovery_source_by_type(db, entry["source_type"])
        # Create source if missing (one per manifest entry)
        if source is None:
            source = DiscoverySource(
                name=entry["source_name"],
                source_type=entry["source_type"],
                language="de",
                country="DE",
                is_active=True,
                metadata_json={"manifest_filename": entry["filename"]},
            )
            db.add(source)
            db.flush()
        if not csv_path.exists():
            results[entry["filename"]] = 0
            continue

        count = import_seed_csv_to_raw_items(db, csv_path, source)
        results[entry["filename"]] = count

    return results
