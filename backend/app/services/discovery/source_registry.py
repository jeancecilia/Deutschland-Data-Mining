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
    {"filename": "professions_de.csv", "source_type": "profession_list", "source_name": "Berufsliste DE"},
    {"filename": "exams_de.csv", "source_type": "exam_list", "source_name": "Prüfungen DE"},
    {"filename": "life_events_de.csv", "source_type": "life_event_list", "source_name": "Lebensereignisse DE"},
    {"filename": "hobbies_de.csv", "source_type": "hobby_list", "source_name": "Hobbys & Haustiere DE"},
    {"filename": "family_topics_de.csv", "source_type": "public_list", "source_name": "Familienthemen DE"},
    {"filename": "senior_topics_de.csv", "source_type": "public_list", "source_name": "Seniorenthemen DE"},
    {"filename": "business_topics_de.csv", "source_type": "public_list", "source_name": "Selbstständigkeit DE"},
    {"filename": "ai_use_cases_de.csv", "source_type": "public_list", "source_name": "KI-Anwendungsfälle DE"},
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
) -> int:
    """Import a seed CSV file into raw_discovery_items.

    CSV format: name,entity_type,priority

    Returns the number of imported items.
    """
    if not csv_path.exists():
        return 0

    now = datetime.now(UTC)
    imported = 0

    with open(csv_path, encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
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

            # Check duplicate by raw_text + source
            existing = db.scalars(
                select(RawDiscoveryItem).where(
                    RawDiscoveryItem.raw_text == name,
                    RawDiscoveryItem.discovery_source_id == source.id,
                )
            ).first()
            if existing is not None:
                continue

            item = RawDiscoveryItem(
                discovery_source_id=source.id,
                raw_text=name,
                language=source.language,
                country=source.country,
                confidence=max(50, min(100, priority)),
                metadata_json={"entity_type_hint": entity_type, "priority": priority} if entity_type else None,
                status="new",
                collected_at=now,
            )
            db.add(item)
            imported += 1

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
        source = get_discovery_source_by_type(db, entry["source_type"])
        if source is None:
            source = db.scalars(
                select(DiscoverySource).where(DiscoverySource.name == entry["source_name"])
            ).first()
        if source is None:
            results[entry["filename"]] = 0
            continue

        count = import_seed_csv_to_raw_items(db, csv_path, source)
        results[entry["filename"]] = count

    return results
