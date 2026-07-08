"""
Relation Builder — builds entity_relations from co-occurrence and dictionary rules.

No Cartesian products. Relations are only created when entities share:
  1. Same raw source / CSV origin (co-occurrence)
  2. Explicit dictionary pair rules
  3. Seed metadata hints
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import (
    DiscoveryEntity,
    DiscoveryEntityRelation,
    DiscoverySource,
    RawDiscoveryItem,
)


# Concrete dictionary pair rules: (source_entity_type, target_entity_type, relation_type)
# These define known valid relationships from domain knowledge.
KNOWN_PAIRS: list[tuple[str, str, str]] = [
    # Profession → Exam
    ("Fachinformatiker", "IHK-Prüfung", "has_exam"),
    ("Elektroniker", "IHK-Prüfung", "has_exam"),
    ("Mechatroniker", "IHK-Prüfung", "has_exam"),
    ("Industriemechaniker", "IHK-Prüfung", "has_exam"),
    ("Kfz-Mechatroniker", "IHK-Prüfung", "has_exam"),
    ("Bürokaufmann", "IHK-Prüfung", "has_exam"),
    ("Industriekaufmann", "IHK-Prüfung", "has_exam"),
    ("Bankkaufmann", "IHK-Prüfung", "has_exam"),
    ("Steuerberater", "Steuererklärung", "has_exam"),
    ("Rechtsanwalt", "Recht", "requires_authority"),
    # Problem → Format
    ("Stress", "Workbook", "suitable_format"),
    ("Stress", "Ratgeber", "suitable_format"),
    ("Angst", "Workbook", "suitable_format"),
    ("Angst", "Ratgeber", "suitable_format"),
    ("Rückenschmerzen", "Workbook", "suitable_format"),
    ("Schlafprobleme", "Tagebuch", "suitable_format"),
    ("Schlafprobleme", "Ratgeber", "suitable_format"),
    # Life event → Format
    ("Umzug", "Checkliste", "suitable_format"),
    ("Hochzeit", "Planer", "suitable_format"),
    ("Schwangerschaft", "Tagebuch", "suitable_format"),
    ("Schwangerschaft", "Ratgeber", "suitable_format"),
    ("Rente", "Ratgeber", "suitable_format"),
    ("Studium", "Lernplaner", "suitable_format"),
    ("Studium", "Planer", "suitable_format"),
    # Topic → Format
    ("Ernährung", "Ratgeber", "suitable_format"),
    ("Ernährung", "Kochbuch", "suitable_format"),
    ("Kochen", "Kochbuch", "suitable_format"),
    ("Fitness", "Trainingsbuch", "suitable_format"),
    ("Fitness", "Planer", "suitable_format"),
    ("Yoga", "Workbook", "suitable_format"),
    ("Hund", "Trainingstagebuch", "suitable_format"),
    ("Hund", "Ratgeber", "suitable_format"),
    ("Garten", "Ratgeber", "suitable_format"),
    ("Garten", "Planer", "suitable_format"),
    # Hobby → Format
    ("Fotografie", "Ratgeber", "suitable_format"),
    ("Nähen", "Workbook", "suitable_format"),
    ("Stricken", "Workbook", "suitable_format"),
    ("Malen", "Workbook", "suitable_format"),
    ("Zeichnen", "Arbeitsbuch", "suitable_format"),
    # Skill → Profession
    ("KI", "Handwerker", "related_to"),
    ("ChatGPT", "Lehrer", "related_to"),
    ("ChatGPT", "Selbstständige", "related_to"),
    ("Excel", "Selbstständige", "related_to"),
    ("Excel", "Bürokaufmann", "related_to"),
    ("Programmieren", "Fachinformatiker", "related_to"),
    # Topic → Audience
    ("ADHS", "Erwachsene", "problem_for"),
    ("ADHS", "Kinder", "problem_for"),
    ("ADHS", "Eltern", "problem_for"),
    ("Demenz", "Senioren", "problem_for"),
    ("Demenz", "Angehörige", "problem_for"),
    ("Pflege", "Angehörige", "problem_for"),
    ("Pflege", "Senioren", "problem_for"),
    ("Schlafprobleme", "Schichtarbeiter", "problem_for"),
    ("Stress", "Pflegekräfte", "problem_for"),
    ("Stress", "Schichtarbeiter", "problem_for"),
    ("Rückenschmerzen", "Pflegekräfte", "problem_for"),
    ("Rückenschmerzen", "Bürokaufmann", "problem_for"),
    ("Ernährung", "Schichtarbeiter", "related_to"),
    ("Ernährung", "Senioren", "related_to"),
    ("Buchhaltung", "Selbstständige", "related_to"),
    ("Steuererklärung", "Selbstständige", "related_to"),
    ("Steuererklärung", "Freelancer", "related_to"),
]


@dataclass
class RelationBuilderResult:
    created: int
    skipped: int
    co_occurrence: int
    dict_pairs: int
    relations: list[DiscoveryEntityRelation]


def _load_existing_relations(db: Session) -> set[tuple[int, int, str]]:
    """Load existing relation keys for dedup."""
    return {
        (r.source_entity_id, r.target_entity_id, r.relation_type)
        for r in db.scalars(select(DiscoveryEntityRelation))
    }


def _entity_index_by_name(entities: list[DiscoveryEntity]) -> dict[str, list[DiscoveryEntity]]:
    """Index entities by casefolded name."""
    index: dict[str, list[DiscoveryEntity]] = {}
    for e in entities:
        key = e.name.casefold()
        index.setdefault(key, []).append(e)
    return index


def build_entity_relations(
    db: Session,
    *,
    limit_per_rule: int = 20,
) -> RelationBuilderResult:
    """Build relations between entities.

    Strategy:
      1. Co-occurrence: entities from the same raw source / CSV origin
      2. Dictionary pairs: explicit known pairs from domain knowledge
    """
    existing = _load_existing_relations(db)
    entities = list(db.scalars(select(DiscoveryEntity)))
    name_index = _entity_index_by_name(entities)

    created = 0
    skipped = 0
    co_occurrence_count = 0
    dict_pair_count = 0
    result_relations: list[DiscoveryEntityRelation] = []

    # ── Strategy 1: Co-occurrence (same raw source origin) ────────────────
    # Group entities by their original source
    source_entities: dict[int, list[DiscoveryEntity]] = {}
    for raw_item in db.scalars(
        select(RawDiscoveryItem).where(RawDiscoveryItem.status.in_(["processed", "new"]))
    ):
        if raw_item.discovery_source_id is None:
            continue
        # Find entities from this raw item
        normalized = raw_item.raw_text.casefold()
        matches = name_index.get(normalized, [])
        for match in matches:
            source_entities.setdefault(raw_item.discovery_source_id, []).append(match)

    # Within each source group, create default relations between entities
    for source_id, source_entity_list in source_entities.items():
        if len(source_entity_list) < 2:
            continue
        # Create "related_to" relations among entities sharing the same source
        for i, source_entity in enumerate(source_entity_list[:limit_per_rule]):
            for target_entity in source_entity_list[i + 1 : i + 6]:
                if source_entity.id == target_entity.id:
                    continue
                rel_type = _infer_relation_from_types(
                    source_entity.entity_type, target_entity.entity_type
                )
                key = (source_entity.id, target_entity.id, rel_type)
                if key in existing:
                    skipped += 1
                    continue
                relation = DiscoveryEntityRelation(
                    source_entity_id=source_entity.id,
                    target_entity_id=target_entity.id,
                    relation_type=rel_type,
                    weight=1.0,
                    confidence=0.55,
                    evidence_source=f"co-occurrence:source_{source_id}",
                )
                db.add(relation)
                existing.add(key)
                result_relations.append(relation)
                created += 1
                co_occurrence_count += 1

    # ── Strategy 2: Dictionary pairs ──────────────────────────────────────
    for source_name, target_name, rel_type in KNOWN_PAIRS:
        source_matches = name_index.get(source_name.casefold(), [])
        target_matches = name_index.get(target_name.casefold(), [])
        if not source_matches or not target_matches:
            continue

        source_entity = source_matches[0]
        target_entity = target_matches[0]
        key = (source_entity.id, target_entity.id, rel_type)
        if key in existing:
            skipped += 1
            continue

        relation = DiscoveryEntityRelation(
            source_entity_id=source_entity.id,
            target_entity_id=target_entity.id,
            relation_type=rel_type,
            weight=1.0,
            confidence=0.80,
            evidence_source=f"dict_pair:{source_name}->{target_name}",
        )
        db.add(relation)
        existing.add(key)
        result_relations.append(relation)
        created += 1
        dict_pair_count += 1

    if created:
        db.commit()
        for rel in result_relations:
            db.refresh(rel)

    return RelationBuilderResult(
        created=created,
        skipped=skipped,
        co_occurrence=co_occurrence_count,
        dict_pairs=dict_pair_count,
        relations=result_relations,
    )


def _infer_relation_from_types(source_type: str, target_type: str) -> str:
    """Infer a relation type from entity type pair."""
    type_pairs = {
        ("profession", "exam"): "has_exam",
        ("exam", "profession"): "has_exam",
        ("profession", "problem"): "has_problem",
        ("problem", "profession"): "problem_for",
        ("audience", "problem"): "has_problem",
        ("problem", "audience"): "problem_for",
        ("topic", "book_format"): "suitable_format",
        ("problem", "book_format"): "suitable_format",
        ("hobby", "book_format"): "suitable_format",
        ("life_event", "book_format"): "suitable_format",
        ("skill", "profession"): "related_to",
        ("profession", "skill"): "related_to",
        ("skill", "audience"): "related_to",
        ("topic", "audience"): "related_to",
        ("audience", "topic"): "related_to",
        ("hobby", "audience"): "related_to",
        ("object", "hobby"): "related_to",
        ("hobby", "object"): "related_to",
        ("life_event", "audience"): "related_to",
    }
    return type_pairs.get((source_type, target_type), "related_to")
