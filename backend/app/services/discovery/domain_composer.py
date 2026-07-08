"""
Domain-Aware Candidate Composer — samples evenly across all imported domains.

Unlike the graph-driven composer, this one:
  1. Gets domains from entity metadata
  2. For each domain, loads topics, audiences, problems
  3. Uses simple reliable templates
  4. Caps candidates per domain for fairness
  5. Stores domain in candidate source_entities (JSONB column)

Note: NicheCandidate has source_entities (JSONB) but no metadata_json column,
so domain is stored as source_entities["domain"].
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import DiscoveryEntity, NicheCandidate
from app.services.discovery.constraint_engine import (
    is_too_generic,
)
from app.services.discovery.entity_normalizer import normalize_entity_name
from app.services.discovery.semantic_compatibility import check_semantic_compatibility

# Simple reliable templates for domain-aware composition
DOMAIN_TEMPLATES = [
    "{topic} für {audience}",
    "{topic} Praxisratgeber für {audience}",
    "{topic} Arbeitsbuch für {audience}",
    "{topic} Checkliste für {audience}",
    "{topic} Planer für {audience}",
    "{topic} Hilfe bei {problem}",
    "{topic} Ratgeber bei {problem}",
    "{topic} Workbook mit Vorlagen",
    "{topic} Schritt-für-Schritt",
]

SAFE_GLOBAL_AUDIENCES = [
    "Anfänger", "Einsteiger", "Erwachsene", "Jugendliche",
    "Senioren", "Eltern", "Berufstätige", "Studierende",
]

SAFE_GLOBAL_PROBLEMS = [
    "Zeitmangel", "Überforderung", "Motivation", "Organisation",
    "Kosten", "Qualität", "Orientierung",
]


@dataclass
class DomainComposeResult:
    created: int
    domains_used: int
    skipped_duplicate: int
    skipped_blocked: int
    skipped_generic: int


def compose_domain_aware_candidates(
    db: Session,
    *,
    limit: int = 10000,
    max_candidates_per_domain: int = 100,
    min_domains: int = 50,
    max_domains: int = 100,
) -> DomainComposeResult:
    """Generate candidates evenly across domains."""
    from sqlalchemy import select as sa_select

    # Get active domains from entity metadata (those with topics)
    domain_rows = db.execute(text(
        "SELECT DISTINCT metadata_json->>'domain' as domain FROM discovery_entities "
        "WHERE metadata_json->>'domain' IS NOT NULL AND metadata_json->>'domain' != '' "
        "AND entity_type = 'topic' "
        "ORDER BY domain LIMIT :max_domains"
    ), {"max_domains": max_domains}).fetchall()
    domains = [str(r[0]) for r in domain_rows if r[0]]

    if len(domains) < min_domains:
        print(f"Only {len(domains)} domains available (need {min_domains}), using all")

    # Load existing normalized names for dedup
    existing_names: set[str] = set(db.scalars(sa_select(NicheCandidate.normalized_name)))

    # Count existing candidates per domain for fairness (domain stored in source_entities JSONB)
    domain_candidate_counts: dict[str, int] = {}
    count_rows = db.execute(text(
        "SELECT source_entities->>'domain' as domain, COUNT(*) "
        "FROM niche_candidates WHERE source_entities->>'domain' IS NOT NULL "
        "GROUP BY domain"
    )).fetchall()
    for row in count_rows:
        domain_candidate_counts[str(row[0])] = int(row[1])

    created_total = 0
    domains_used = 0
    skipped_duplicate = 0
    skipped_blocked = 0
    skipped_generic = 0

    for domain in domains:
        if created_total >= limit:
            break

        # Fairness: skip domains already at cap
        existing_for_domain = domain_candidate_counts.get(domain, 0)
        if existing_for_domain >= max_candidates_per_domain:
            continue

        remaining_slots = max_candidates_per_domain - existing_for_domain

        # Get topics in this domain
        topic_rows = db.execute(text(
            "SELECT id, name FROM discovery_entities "
            "WHERE metadata_json->>'domain' = :domain AND entity_type = 'topic' "
            "ORDER BY confidence DESC LIMIT 200"
        ), {"domain": domain}).fetchall()
        if not topic_rows:
            continue

        # Get audiences in this domain (or global fallback)
        aud_rows = db.execute(text(
            "SELECT id, name FROM discovery_entities "
            "WHERE metadata_json->>'domain' = :domain AND entity_type = 'audience' "
            "LIMIT 20"
        ), {"domain": domain}).fetchall()

        # Get problems in this domain (or global fallback)
        prob_rows = db.execute(text(
            "SELECT id, name FROM discovery_entities "
            "WHERE metadata_json->>'domain' = :domain AND entity_type = 'problem' "
            "LIMIT 50"
        ), {"domain": domain}).fetchall()

        topics = [(r[0], r[1]) for r in topic_rows]
        audiences = [(r[0], r[1]) for r in aud_rows] if aud_rows else []
        problems = [(r[0], r[1]) for r in prob_rows] if prob_rows else []

        created_for_domain = 0

        for topic_id, topic_name in topics[:50]:
            if created_total >= limit or created_for_domain >= remaining_slots:
                break

            target_audiences = audiences[:5] if audiences else [
                (0, a) for a in SAFE_GLOBAL_AUDIENCES[:3]
            ]
            for aud_id, aud_name in target_audiences:
                if created_total >= limit or created_for_domain >= remaining_slots:
                    break

                for tpl in DOMAIN_TEMPLATES[:6]:
                    if created_total >= limit or created_for_domain >= remaining_slots:
                        break

                    if "{audience}" in tpl and not aud_name:
                        continue
                    if "{problem}" in tpl and not problems:
                        continue

                    phrase = tpl.format(
                        topic=topic_name,
                        audience=aud_name,
                        problem=problems[0][1] if problems and "{problem}" in tpl else "",
                    )

                    normalized = normalize_entity_name(phrase)
                    if not normalized:
                        continue
                    if normalized in existing_names:
                        skipped_duplicate += 1
                        continue
                    if is_too_generic(phrase):
                        skipped_generic += 1
                        continue

                    compat = check_semantic_compatibility(topic_name, aud_name)
                    if not compat.compatible:
                        skipped_blocked += 1
                        continue

                    se: dict[str, object] = {"topic": topic_id, "domain": domain}
                    if aud_id > 0:
                        se["audience"] = aud_id

                    candidate = NicheCandidate(
                        candidate_name=phrase,
                        normalized_name=normalized,
                        main_topic_entity_id=topic_id,
                        audience_entity_id=aud_id if aud_id > 0 else None,
                        problem_entity_id=problems[0][0] if problems and "{problem}" in tpl else None,
                        book_class_guess="sachbuch",
                        language="de",
                        marketplace="amazon.de",
                        generation_template=f"domain_aware:{tpl[:40]}",
                        source_entities=se,
                        confidence=55,
                        risk_level="low",
                        status="new",
                    )
                    db.add(candidate)
                    db.flush()
                    existing_names.add(normalized)
                    created_for_domain += 1
                    created_total += 1

            # Topic + problem templates
            if problems and created_for_domain < remaining_slots:
                for prob_id, prob_name in problems[:3]:
                    if created_total >= limit or created_for_domain >= remaining_slots:
                        break
                    for tpl in DOMAIN_TEMPLATES[5:]:
                        if "{problem}" not in tpl:
                            continue
                        phrase = tpl.format(topic=topic_name, audience="", problem=prob_name)
                        normalized = normalize_entity_name(phrase)
                        if not normalized or normalized in existing_names:
                            if normalized in existing_names:
                                skipped_duplicate += 1
                            continue
                        if is_too_generic(phrase):
                            skipped_generic += 1
                            continue

                        candidate = NicheCandidate(
                            candidate_name=phrase,
                            normalized_name=normalized,
                            main_topic_entity_id=topic_id,
                            problem_entity_id=prob_id,
                            book_class_guess="sachbuch",
                            language="de",
                            marketplace="amazon.de",
                            generation_template=f"domain_aware:{tpl[:40]}",
                            source_entities={"topic": topic_id, "problem": prob_id, "domain": domain},
                            confidence=50,
                            risk_level="low",
                            status="new",
                        )
                        db.add(candidate)
                        db.flush()
                        existing_names.add(normalized)
                        created_for_domain += 1
                        created_total += 1

        if created_for_domain > 0:
            domains_used += 1

    if created_total:
        db.commit()

    return DomainComposeResult(
        created=created_total,
        domains_used=domains_used,
        skipped_duplicate=skipped_duplicate,
        skipped_blocked=skipped_blocked,
        skipped_generic=skipped_generic,
    )
