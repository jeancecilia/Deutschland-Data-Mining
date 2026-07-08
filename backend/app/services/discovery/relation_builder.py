"""
Relation Builder — builds entity_relations from dictionaries and co-occurrence.

Creates typed edges in the Topic Graph:
  - has_problem, works_in_context, suitable_format, has_exam, etc.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import DiscoveryEntity, DiscoveryEntityRelation


# Known relation-building rules: (source_entity_type, relation_type, target_entity_type)
# These are seeded from domain knowledge about German KDP niches.
RELATION_RULES: list[tuple[str, str, str, float]] = [
    # Audience + problem
    ("audience", "has_problem", "problem", 0.7),
    ("profession", "has_problem", "problem", 0.7),
    # Profession + exam
    ("profession", "has_exam", "exam", 0.8),
    # Profession + skill
    ("profession", "related_to", "skill", 0.6),
    # Problem + format
    ("problem", "suitable_format", "book_format", 0.6),
    # Topic + format
    ("topic", "suitable_format", "book_format", 0.5),
    # Hobby + format
    ("hobby", "suitable_format", "book_format", 0.5),
    # Life event + format
    ("life_event", "suitable_format", "book_format", 0.6),
    # Problem + audience (reverse)
    ("problem", "problem_for", "audience", 0.5),
    ("problem", "problem_for", "profession", 0.5),
    # Topic + audience
    ("topic", "related_to", "audience", 0.4),
    ("skill", "related_to", "profession", 0.6),
    ("skill", "related_to", "audience", 0.4),
    # Hobby + audience
    ("hobby", "related_to", "audience", 0.4),
    # Life event + audience
    ("life_event", "related_to", "audience", 0.5),
    # Object + hobby
    ("object", "related_to", "hobby", 0.7),
]


@dataclass
class RelationBuilderResult:
    created: int
    skipped: int
    relations: list[DiscoveryEntityRelation]


def _entity_type_map(db: Session) -> dict[str, list[DiscoveryEntity]]:
    """Group all active entities by type."""
    entities = list(db.scalars(select(DiscoveryEntity)))
    mapping: dict[str, list[DiscoveryEntity]] = {}
    for entity in entities:
        mapping.setdefault(entity.entity_type, []).append(entity)
    return mapping


def build_entity_relations(
    db: Session,
    *,
    limit_per_rule: int = 20,
) -> RelationBuilderResult:
    """Build relations between entities using rule-based matching.

    For each rule (source_type, relation_type, target_type), pairs top-N entities
    from each group and creates relations, skipping duplicates.
    """
    type_map = _entity_type_map(db)

    # Load existing relations for dedup
    existing_relations: set[tuple[int, int, str]] = set()
    for rel in db.scalars(select(DiscoveryEntityRelation)):
        existing_relations.add((rel.source_entity_id, rel.target_entity_id, rel.relation_type))

    created = 0
    skipped = 0
    result_relations: list[DiscoveryEntityRelation] = []

    for source_type, relation_type, target_type, confidence in RELATION_RULES:
        sources = type_map.get(source_type, [])
        targets = type_map.get(target_type, [])
        if not sources or not targets:
            continue

        # Take top-N from each side
        sources_sorted = sorted(sources, key=lambda e: e.confidence, reverse=True)[:limit_per_rule]
        targets_sorted = sorted(targets, key=lambda e: e.confidence, reverse=True)[:limit_per_rule]

        for source in sources_sorted:
            for target in targets_sorted:
                if source.id == target.id:
                    continue
                key = (source.id, target.id, relation_type)
                if key in existing_relations:
                    skipped += 1
                    continue

                relation = DiscoveryEntityRelation(
                    source_entity_id=source.id,
                    target_entity_id=target.id,
                    relation_type=relation_type,
                    weight=1.0,
                    confidence=confidence,
                    evidence_source=f"rule:{source_type}->{target_type}",
                )
                db.add(relation)
                existing_relations.add(key)
                result_relations.append(relation)
                created += 1

    if created:
        db.commit()
        for rel in result_relations:
            db.refresh(rel)

    return RelationBuilderResult(
        created=created,
        skipped=skipped,
        relations=result_relations,
    )
