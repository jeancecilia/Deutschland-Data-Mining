"""
Entity Extractor — extracts structured DiscoveryEntities from RawDiscoveryItems.

Hybrid approach:
  1. Dictionary-based recognition (entity_type_hint from metadata)
  2. Rule-based pattern matching (German word patterns)
  3. Normalization + deduplication
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import DiscoveryEntity, DiscoveryEntityAlias, RawDiscoveryItem
from app.services.discovery.entity_normalizer import normalize_entity_name


# Known entity_type hints from CSV metadata
ENTITY_TYPE_MAP: dict[str, str] = {
    "profession": "profession",
    "exam": "exam",
    "life_event": "life_event",
    "hobby": "hobby",
    "object": "object",
    "topic": "topic",
    "audience": "audience",
    "skill": "skill",
    "problem": "problem",
    "book_format": "book_format",
}

# German pattern → entity_type rules
PATTERN_RULES: list[tuple[str, str]] = [
    # Book formats
    ("tagebuch", "book_format"),
    ("logbuch", "book_format"),
    ("tracker", "book_format"),
    ("planer", "book_format"),
    ("journal", "book_format"),
    ("checkliste", "book_format"),
    ("ratgeber", "book_format"),
    ("workbook", "book_format"),
    ("leitfaden", "book_format"),
    ("handbuch", "book_format"),
    ("praxisbuch", "book_format"),
    ("arbeitsbuch", "book_format"),
    ("vorlagenbuch", "book_format"),
    # Exam indicators
    ("prüfung", "exam"),
    ("abschlussprüfung", "exam"),
    ("abitur", "exam"),
    ("test", "exam"),
    ("zertifikat", "exam"),
    ("führerschein", "exam"),
    # Professions
    ("pfleger", "profession"),
    ("therapeut", "profession"),
    ("informatiker", "profession"),
    ("entwickler", "profession"),
    ("ingenieur", "profession"),
    ("berater", "profession"),
    ("meister", "profession"),
    ("kaufmann", "profession"),
    ("fahrer", "profession"),
    # Life events
    ("wohnung", "life_event"),
    ("umzug", "life_event"),
    ("hochzeit", "life_event"),
    ("scheidung", "life_event"),
    ("schwangerschaft", "life_event"),
    ("geburt", "life_event"),
    ("rente", "life_event"),
    ("ruhestand", "life_event"),
    ("pflegefall", "life_event"),
    ("todesfall", "life_event"),
    ("gründung", "life_event"),
    # Audience
    ("senioren", "audience"),
    ("anfänger", "audience"),
    ("einsteiger", "audience"),
    ("eltern", "audience"),
    ("kinder", "audience"),
    ("selbstständige", "audience"),
    ("schüler", "audience"),
    ("studenten", "audience"),
    # Hobbies
    ("hund", "hobby"),
    ("garten", "hobby"),
    ("kochen", "hobby"),
    ("backen", "hobby"),
    ("yoga", "hobby"),
    ("fitness", "hobby"),
    ("wandern", "hobby"),
    ("fotografie", "hobby"),
    ("nähen", "hobby"),
    ("stricken", "hobby"),
    ("angeln", "hobby"),
    ("camping", "hobby"),
    # Skills
    ("ki", "skill"),
    ("chatgpt", "skill"),
    ("programmieren", "skill"),
    ("excel", "skill"),
    # Problems
    ("stress", "problem"),
    ("angst", "problem"),
    ("schmerz", "problem"),
    ("überforderung", "problem"),
    ("zeitmangel", "problem"),
    ("schlaflos", "problem"),
    ("einsam", "problem"),
]


@dataclass
class EntityExtractionResult:
    created: int
    updated: int
    skipped: int
    entities: list[DiscoveryEntity]


def _infer_entity_type(raw_text: str, metadata: dict | None) -> str | None:
    """Infer entity_type from metadata hint first, then pattern rules."""
    if metadata:
        hint = metadata.get("entity_type_hint")
        if hint and hint in ENTITY_TYPE_MAP:
            return ENTITY_TYPE_MAP[hint]

    lowered = raw_text.casefold()
    for pattern, entity_type in PATTERN_RULES:
        if pattern in lowered:
            return entity_type

    return None


def extract_entities_from_raw_items(
    db: Session,
    *,
    limit: int = 500,
) -> EntityExtractionResult:
    """Process unprocessed raw_discovery_items and extract/upsert entities.

    Only processes items with status='new'.
    """
    items = list(
        db.scalars(
            select(RawDiscoveryItem)
            .where(RawDiscoveryItem.status == "new")
            .order_by(RawDiscoveryItem.confidence.desc())
            .limit(limit)
        )
    )

    # Load existing entities for dedup
    existing_entities: dict[str, DiscoveryEntity] = {}
    for entity in db.scalars(select(DiscoveryEntity)):
        key = f"{entity.normalized_name}|{entity.entity_type}|{entity.language}"
        existing_entities[key] = entity

    # Track aliases in-memory to avoid duplicate key violations within a batch
    # (SQLAlchemy select() only sees committed rows, not session.new objects)
    known_aliases: set[tuple[int, str]] = set()
    for alias in db.scalars(select(DiscoveryEntityAlias)):
        known_aliases.add((alias.entity_id, alias.alias))

    created = 0
    updated = 0
    skipped = 0
    result_entities: list[DiscoveryEntity] = []

    for item in items:
        raw_text = item.raw_text.strip()
        if not raw_text or len(raw_text) < 2:
            item.status = "ignored"
            item.processed_at = item.collected_at
            db.add(item)
            skipped += 1
            continue

        entity_type = _infer_entity_type(raw_text, item.metadata_json)
        if entity_type is None:
            entity_type = "topic"  # fallback

        normalized = normalize_entity_name(raw_text)
        if not normalized or len(normalized) < 2:
            item.status = "ignored"
            item.processed_at = item.collected_at
            db.add(item)
            skipped += 1
            continue

        key = f"{normalized}|{entity_type}|{item.language}"
        current_entity: DiscoveryEntity | None = existing_entities.get(key)

        if current_entity is not None:
            # Bump source_count on existing entity
            current_entity.source_count = (current_entity.source_count or 1) + 1
            current_entity.confidence = min(1.0, current_entity.confidence + 0.05)
            db.add(current_entity)
            updated += 1
        else:
            current_entity = DiscoveryEntity(
                name=raw_text[:255],
                normalized_name=normalized,
                entity_type=entity_type,
                language=item.language,
                country=item.country,
                confidence=0.6,
                source_count=1,
                metadata_json=item.metadata_json,
            )
            db.add(current_entity)
            db.flush()
            existing_entities[key] = current_entity
            created += 1

        result_entities.append(current_entity)

        # Store original text as alias if different from normalized name
        alias_text = raw_text[:255]
        if raw_text.casefold() != normalized and current_entity.id:
            alias_key = (current_entity.id, alias_text)
            if alias_key not in known_aliases:
                db.add(DiscoveryEntityAlias(
                    entity_id=current_entity.id,
                    alias=alias_text,
                    language=item.language,
                ))
                known_aliases.add(alias_key)

        item.status = "processed"
        item.processed_at = item.collected_at
        db.add(item)

    db.commit()
    for entity in result_entities:
        db.refresh(entity)

    return EntityExtractionResult(
        created=created,
        updated=updated,
        skipped=skipped,
        entities=result_entities,
    )
