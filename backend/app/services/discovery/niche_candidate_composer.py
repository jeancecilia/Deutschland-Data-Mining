"""
Niche Candidate Composer — generates KDP niche candidates from entities + templates.

Takes entities grouped by type, applies templates, checks constraints,
and produces NicheCandidate records.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from itertools import product

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import DiscoveryEntity, NicheCandidate
from app.services.discovery.constraint_engine import (
    check_constraint,
    CONSTRAINT_BLOCK,
    CONSTRAINT_FLAG_RISK,
    CONSTRAINT_DOWNGRADE,
    get_risk_level,
    is_too_generic,
)
from app.services.discovery.entity_normalizer import normalize_entity_name
from app.services.discovery.template_engine import (
    DEFAULT_TEMPLATES,
    template_engine,
)


@dataclass
class ComposeBatch:
    created: int
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
    """Generate niche candidates from entities using templates and constraints.

    Steps:
      1. Load entities grouped by type
      2. For each template, find matching entity combinations
      3. Apply constraint engine
      4. Generate phrase, check for duplicates/generic
      5. Persist NicheCandidate records
    """
    # Load all entities
    entities = list(db.scalars(select(DiscoveryEntity)))
    entities_by_type: dict[str, list[DiscoveryEntity]] = {}
    for entity in entities:
        entities_by_type.setdefault(entity.entity_type, []).append(entity)

    # Load existing candidates for dedup
    existing_names: set[str] = {
        c.normalized_name
        for c in db.scalars(select(NicheCandidate.normalized_name))
    }

    created = 0
    skipped_blocked = 0
    skipped_duplicate = 0
    skipped_generic = 0
    result_candidates: list[NicheCandidate] = []

    for tpl in DEFAULT_TEMPLATES:
        if created >= limit:
            break

        tpl_count = 0

        # Collect entity pools for each required type
        pools: list[list[DiscoveryEntity]] = []
        for req_type in tpl.required_types:
            pool = entities_by_type.get(req_type, [])
            if not pool:
                pools = []  # Can't fulfill this template
                break
            # Shuffle to get diverse combinations
            shuffled = sorted(pool, key=lambda e: e.confidence, reverse=True)[:15]
            pools.append(shuffled)

        if not pools:
            continue

        # Generate combinations
        for combo in product(*pools):
            if tpl_count >= max_per_template or created >= limit:
                break

            # Build type→name mapping
            type_values: dict[str, str] = {}
            entity_ids: dict[str, int] = {}
            entity_types_set: list[str] = []

            for i, req_type in enumerate(tpl.required_types):
                entity = combo[i]
                type_values[req_type] = entity.name
                entity_ids[req_type] = entity.id
                if req_type not in entity_types_set:
                    entity_types_set.append(req_type)

            # Check optional types
            for opt_type in tpl.optional_types:
                opt_pool = entities_by_type.get(opt_type, [])
                if opt_pool and random.random() < 0.3:
                    opt_entity = random.choice(opt_pool)
                    type_values[opt_type] = opt_entity.name
                    entity_ids[opt_type] = opt_entity.id
                    if opt_type not in entity_types_set:
                        entity_types_set.append(opt_type)

            # Constraint check
            constraint = check_constraint(entity_types_set, entity_types_set)
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
            risk = get_risk_level(entity_types_set)
            if constraint.action == CONSTRAINT_FLAG_RISK:
                risk = "high" if risk == "medium" else "medium"

            book_class = tpl.book_type_hint
            if constraint.action == CONSTRAINT_DOWNGRADE:
                book_class = "medium_content"

            # Create candidate
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
            tpl_count += 1

    if created:
        db.commit()
        for c in result_candidates:
            db.refresh(c)

    return ComposeBatch(
        created=created,
        skipped_blocked=skipped_blocked,
        skipped_duplicate=skipped_duplicate,
        skipped_generic=skipped_generic,
        candidates=result_candidates,
    )
