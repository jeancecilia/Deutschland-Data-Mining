"""
Niche Candidate Composer — graph-driven niche generation.

Uses discovery_entity_relations (Topic Graph) to find valid entity combinations,
then applies templates to generate candidate phrases.

Key difference from v1: only combines entities that have a real graph edge,
NOT Cartesian products of entity type pools.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import (
    DiscoveryEntity,
    DiscoveryEntityRelation,
    NicheCandidate,
)
from app.services.discovery.constraint_engine import (
    CONSTRAINT_BLOCK,
    CONSTRAINT_DOWNGRADE,
    CONSTRAINT_FLAG_RISK,
    check_constraint,
    get_risk_level,
    is_too_generic,
)
from app.services.discovery.entity_normalizer import normalize_entity_name
from app.services.discovery.template_engine import DEFAULT_TEMPLATES, template_engine


@dataclass
class ComposeBatch:
    created: int
    skipped_no_relation: int
    skipped_blocked: int
    skipped_duplicate: int
    skipped_generic: int
    candidates: list[NicheCandidate]


def compose_niche_candidates(
    db: Session,
    *,
    limit: int = 500,
    max_per_template: int = 50,
) -> ComposeBatch:
    """Generate niche candidates using the Topic Graph.

    For each entity with graph relations:
      1. Walk its outgoing relations to find connected entities
      2. Try to match a template that fits the connected entity types
      3. Render phrase, check constraints, deduplicate
    """
    # Load entities
    entities = list(db.scalars(select(DiscoveryEntity)))
    entity_map: dict[int, DiscoveryEntity] = {e.id: e for e in entities}

    # Load active relations
    relations = list(db.scalars(select(DiscoveryEntityRelation)))

    # Build adjacency: entity_id → list of (target_entity, relation_type)
    adjacency: dict[int, list[tuple[DiscoveryEntity, str]]] = {}
    for rel in relations:
        target = entity_map.get(rel.target_entity_id)
        if target is None:
            continue
        adjacency.setdefault(rel.source_entity_id, []).append((target, rel.relation_type))

    # Also add reverse edges so both directions are traversable
    for rel in relations:
        source = entity_map.get(rel.source_entity_id)
        if source is None:
            continue
        # Reverse the relation type
        reverse_type = _reverse_relation_type(rel.relation_type)
        adjacency.setdefault(rel.target_entity_id, []).append((source, reverse_type))

    # Load existing candidates for dedup
    existing_names: set[str] = set(db.scalars(select(NicheCandidate.normalized_name)))

    created = 0
    skipped_no_relation = 0
    skipped_blocked = 0
    skipped_duplicate = 0
    skipped_generic = 0
    result_candidates: list[NicheCandidate] = []

    # Try each entity as a starting point
    for entity in entities:
        if created >= limit:
            break

        neighbors = adjacency.get(entity.id, [])
        if not neighbors:
            continue

        # Try combining this entity with its graph neighbors
        for neighbor, rel_type in neighbors:
            if created >= limit:
                break

            # Skip self
            if neighbor.id == entity.id:
                continue

            # Build a small entity pool: [entity, neighbor]
            pool = [entity, neighbor]
            entity_types_set = [entity.entity_type, neighbor.entity_type]

            # Try to find a template matching these types
            for tpl in DEFAULT_TEMPLATES:
                if created >= limit:
                    break

                # Check if template's required types are in our pool
                required_types = set(tpl.required_types)
                pool_types = set(entity_types_set)
                if not required_types.issubset(pool_types):
                    continue

                # Build values dict for template rendering
                type_values: dict[str, str] = {}
                entity_ids: dict[str, int] = {}

                # Assign each entity to the first matching required type
                assigned_types: set[str] = set()
                for e in pool:
                    e_type = e.entity_type
                    for req_type in required_types:
                        if req_type not in assigned_types and e_type == req_type:
                            type_values[req_type] = e.name
                            entity_ids[req_type] = e.id
                            assigned_types.add(req_type)
                            break

                # Also map the other entity to a compatible type if possible
                if len(assigned_types) < len(pool):
                    for e in pool:
                        e_type = e.entity_type
                        if e_type not in assigned_types:
                            # Use as optional context
                            type_values[e_type] = e.name
                            entity_ids[e_type] = e.id

                # Check we have all required types
                if not all(req in type_values for req in required_types):
                    continue
                if not all("{" + req + "}" in tpl.pattern for req in required_types):
                    # Skip templates that don't actually use all types
                    pass

                # Constraint check
                constraint = check_constraint(list(type_values.keys()), list(type_values.keys()))
                if constraint.action == CONSTRAINT_BLOCK:
                    skipped_blocked += 1
                    continue

                # Render phrase
                phrase = template_engine.render(tpl, type_values)
                normalized = normalize_entity_name(phrase)

                # Duplicate check
                if normalized in existing_names:
                    skipped_duplicate += 1
                    continue

                # Generic check
                if is_too_generic(phrase):
                    skipped_generic += 1
                    continue

                # Determine risk
                risk = get_risk_level(list(type_values.keys()))
                if constraint.action == CONSTRAINT_FLAG_RISK:
                    risk = "high" if risk == "medium" else "medium"

                book_class = tpl.book_type_hint
                if constraint.action == CONSTRAINT_DOWNGRADE:
                    book_class = "medium_content"

                candidate = NicheCandidate(
                    candidate_name=phrase,
                    normalized_name=normalized,
                    main_topic_entity_id=entity_ids.get("topic") or entity_ids.get("problem") or entity_ids.get("hobby") or entity_ids.get("object"),
                    audience_entity_id=entity_ids.get("audience") or entity_ids.get("profession"),
                    problem_entity_id=entity_ids.get("problem"),
                    format_entity_id=entity_ids.get("book_format"),
                    book_class_guess=book_class,
                    language="de",
                    marketplace="amazon.de",
                    generation_template=tpl.name,
                    source_entities=entity_ids,
                    confidence=max(30, min(95, tpl.priority)),
                    risk_level=risk,
                    status="new",
                )
                db.add(candidate)
                db.flush()
                existing_names.add(normalized)
                result_candidates.append(candidate)
                created += 1

    if created:
        db.commit()
        for c in result_candidates:
            db.refresh(c)

    return ComposeBatch(
        created=created,
        skipped_no_relation=skipped_no_relation,
        skipped_blocked=skipped_blocked,
        skipped_duplicate=skipped_duplicate,
        skipped_generic=skipped_generic,
        candidates=result_candidates,
    )


def _reverse_relation_type(rel_type: str) -> str:
    """Get the reverse direction of a relation type."""
    reverse_map = {
        "has_problem": "problem_for",
        "problem_for": "has_problem",
        "has_exam": "exam_for",
        "exam_for": "has_exam",
        "suitable_format": "format_for",
        "format_for": "suitable_format",
        "works_in_context": "context_for",
        "context_for": "works_in_context",
        "has_subtopic": "subtopic_of",
        "subtopic_of": "has_subtopic",
        "has_life_event": "life_event_of",
        "life_event_of": "has_life_event",
        "has_use_case": "use_case_for",
        "use_case_for": "has_use_case",
        "belongs_to_audience": "includes_audience",
        "includes_audience": "belongs_to_audience",
        "belongs_to_profession": "includes_profession",
        "related_to": "related_to",
        "requires_authority": "authority_for",
        "high_risk_topic": "high_risk_topic",
        "low_risk_topic": "low_risk_topic",
    }
    return reverse_map.get(rel_type, "related_to")
