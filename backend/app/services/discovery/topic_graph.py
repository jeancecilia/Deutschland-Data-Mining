"""
Topic Graph — query helpers for the entity-relation graph.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import DiscoveryEntity, DiscoveryEntityRelation


@dataclass
class TopicGraphQuery:
    entity_count: int
    relation_count: int
    entity_types: dict[str, int]


def get_entity_graph_overview(db: Session) -> TopicGraphQuery:
    """Return counts for the topic graph."""
    entity_count = db.scalar(select(DiscoveryEntity).limit(1))
    entity_count = len(list(db.scalars(select(DiscoveryEntity.id).limit(10000))))

    relation_count = len(list(db.scalars(select(DiscoveryEntityRelation.id).limit(10000))))

    type_counts: dict[str, int] = {}
    for row in db.execute(
        select(DiscoveryEntity.entity_type, DiscoveryEntity.id)
    ).all():
        entity_type = row[0]
        type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

    return TopicGraphQuery(
        entity_count=entity_count,
        relation_count=relation_count,
        entity_types=type_counts,
    )


def get_entities_by_type(db: Session, entity_type: str | None = None) -> list[DiscoveryEntity]:
    """Return entities, optionally filtered by type."""
    stmt = select(DiscoveryEntity).order_by(DiscoveryEntity.confidence.desc())
    if entity_type:
        stmt = stmt.where(DiscoveryEntity.entity_type == entity_type)
    return list(db.scalars(stmt.limit(200)))


def get_graph_neighbors(
    db: Session,
    entity_id: int,
    *,
    relation_type: str | None = None,
    limit: int = 50,
) -> dict[str, list[dict]]:
    """Return incoming and outgoing relations for an entity.

    Returns:
        {"outgoing": [...], "incoming": [...]}
        Each entry: {"entity_id", "entity_name", "entity_type", "relation_type", "weight", "confidence"}
    """
    entity = db.get(DiscoveryEntity, entity_id)
    if entity is None:
        return {"outgoing": [], "incoming": []}

    # Load all entities for name resolution
    entity_map: dict[int, DiscoveryEntity] = {
        e.id: e for e in db.scalars(select(DiscoveryEntity))
    }

    outgoing = list(
        db.scalars(
            select(DiscoveryEntityRelation)
            .where(DiscoveryEntityRelation.source_entity_id == entity_id)
            .order_by(DiscoveryEntityRelation.weight.desc())
            .limit(limit)
        )
    )
    incoming = list(
        db.scalars(
            select(DiscoveryEntityRelation)
            .where(DiscoveryEntityRelation.target_entity_id == entity_id)
            .order_by(DiscoveryEntityRelation.weight.desc())
            .limit(limit)
        )
    )

    if relation_type:
        outgoing = [r for r in outgoing if r.relation_type == relation_type]
        incoming = [r for r in incoming if r.relation_type == relation_type]

    def _serialize(rel: DiscoveryEntityRelation, target_is_target: bool) -> dict:
        target_id = rel.target_entity_id if target_is_target else rel.source_entity_id
        target_entity = entity_map.get(target_id)
        return {
            "entity_id": target_id,
            "entity_name": target_entity.name if target_entity else "?",
            "entity_type": target_entity.entity_type if target_entity else "?",
            "relation_type": rel.relation_type,
            "weight": rel.weight,
            "confidence": rel.confidence,
        }

    return {
        "outgoing": [_serialize(r, True) for r in outgoing],
        "incoming": [_serialize(r, False) for r in incoming],
    }
