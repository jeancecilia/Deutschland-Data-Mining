"""
Relation Builder — builds entity_relations from co-occurrence, dictionary rules,
and domain-based clustering.

All strategies now use targeted SQL queries — no full entity table scans.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.discovery_pipeline import (
    DiscoveryEntity,
    DiscoveryEntityRelation,
)

# Dictionary pair rules: (source_entity_name, target_entity_name, relation_type)
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
    domain_relations: int = 0


def _load_existing_relations(db: Session) -> set[tuple[int, int, str]]:
    """Load existing relation keys for dedup."""
    return {
        (r.source_entity_id, r.target_entity_id, r.relation_type)
        for r in db.scalars(select(DiscoveryEntityRelation))
    }


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


def build_entity_relations(
    db: Session,
    *,
    limit_per_rule: int = 20,
    max_per_domain: int = 200,
    max_domains: int = 1000,
) -> RelationBuilderResult:
    """Build relations between entities using SQL-optimized strategies.

    Strategy 1: Dictionary pairs (fast name lookups)
    Strategy 2: Domain-based clustering (topic↔audience, topic↔problem within same domain)
    Strategy 3: Cross-type relations between non-topic entities (professions, exams, etc.)
    """
    existing = _load_existing_relations(db)
    created = 0
    skipped = 0
    dict_pair_count = 0
    domain_relations_count = 0
    co_occurrence_count = 0
    result_relations: list[DiscoveryEntityRelation] = []

    # ── Strategy 1: Dictionary pairs ──────────────────────────────────
    for source_name, target_name, rel_type in KNOWN_PAIRS:
        source_rows = db.execute(
            text("SELECT id FROM discovery_entities WHERE LOWER(name) = LOWER(:name) LIMIT 1"),
            {"name": source_name}
        ).fetchall()
        target_rows = db.execute(
            text("SELECT id FROM discovery_entities WHERE LOWER(name) = LOWER(:name) LIMIT 1"),
            {"name": target_name}
        ).fetchall()
        if not source_rows or not target_rows:
            continue

        sid, tid = source_rows[0][0], target_rows[0][0]
        key = (sid, tid, rel_type)
        if key in existing:
            skipped += 1
            continue

        relation = DiscoveryEntityRelation(
            source_entity_id=sid,
            target_entity_id=tid,
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

    # ── Strategy 2: Domain-based clustering ───────────────────────────
    # Get domains from entity metadata
    domain_rows = db.execute(text(
        "SELECT DISTINCT metadata_json->>'domain' as domain FROM discovery_entities "
        "WHERE metadata_json->>'domain' IS NOT NULL AND metadata_json->>'domain' != '' "
        "LIMIT :max_domains"
    ), {"max_domains": max_domains}).fetchall()
    domains = [str(r[0]) for r in domain_rows if r[0]]

    for domain in domains:
        # Topics in this domain
        topic_rows = db.execute(text(
            "SELECT id FROM discovery_entities "
            "WHERE metadata_json->>'domain' = :domain AND entity_type = 'topic' "
            "LIMIT :limit"
        ), {"domain": domain, "limit": max_per_domain}).fetchall()
        topic_ids = [r[0] for r in topic_rows]

        # Audiences in this domain
        aud_rows = db.execute(text(
            "SELECT id FROM discovery_entities "
            "WHERE metadata_json->>'domain' = :domain AND entity_type = 'audience' "
            "LIMIT :limit"
        ), {"domain": domain, "limit": max_per_domain // 5}).fetchall()
        audience_ids = [r[0] for r in aud_rows]

        # Problems in this domain
        prob_rows = db.execute(text(
            "SELECT id FROM discovery_entities "
            "WHERE metadata_json->>'domain' = :domain AND entity_type = 'problem' "
            "LIMIT :limit"
        ), {"domain": domain, "limit": max_per_domain // 5}).fetchall()
        problem_ids = [r[0] for r in prob_rows]

        # Topic → Audience (within domain)
        for tid in topic_ids[:max_per_domain // 10]:
            for aid in audience_ids[:5]:
                key = (tid, aid, "related_to")
                if key in existing:
                    skipped += 1
                    continue
                relation = DiscoveryEntityRelation(
                    source_entity_id=tid,
                    target_entity_id=aid,
                    relation_type="related_to",
                    weight=1.0,
                    confidence=0.65,
                    evidence_source=f"domain:{domain}",
                )
                db.add(relation)
                existing.add(key)
                result_relations.append(relation)
                created += 1
                domain_relations_count += 1

        # Topic → Problem (within domain)
        for tid in topic_ids[:max_per_domain // 10]:
            for pid in problem_ids[:3]:
                key = (tid, pid, "has_problem")
                if key in existing:
                    skipped += 1
                    continue
                relation = DiscoveryEntityRelation(
                    source_entity_id=tid,
                    target_entity_id=pid,
                    relation_type="has_problem",
                    weight=1.0,
                    confidence=0.60,
                    evidence_source=f"domain:{domain}",
                )
                db.add(relation)
                existing.add(key)
                result_relations.append(relation)
                created += 1
                domain_relations_count += 1

    # ── Strategy 3: Cross-type relations (non-topic entities) ─────────
    # Profession ↔ Exam
    prof_rows = db.execute(text(
        "SELECT id FROM discovery_entities WHERE entity_type = 'profession' LIMIT :limit"
    ), {"limit": max_per_domain}).fetchall()
    exam_rows = db.execute(text(
        "SELECT id FROM discovery_entities WHERE entity_type = 'exam' LIMIT :limit"
    ), {"limit": max_per_domain}).fetchall()
    for pid in [r[0] for r in prof_rows][:max_per_domain // 10]:
        for eid in [r[0] for r in exam_rows][:5]:
            key = (pid, eid, "has_exam")
            if key in existing:
                skipped += 1
                continue
            relation = DiscoveryEntityRelation(
                source_entity_id=pid,
                target_entity_id=eid,
                relation_type="has_exam",
                weight=1.0,
                confidence=0.50,
                evidence_source="type_cross:profession_exam",
            )
            db.add(relation)
            existing.add(key)
            result_relations.append(relation)
            created += 1
            co_occurrence_count += 1

    # Problem ↔ Book Format
    prob_rows2 = db.execute(text(
        "SELECT id FROM discovery_entities WHERE entity_type = 'problem' LIMIT :limit"
    ), {"limit": max_per_domain}).fetchall()
    fmt_rows = db.execute(text(
        "SELECT id FROM discovery_entities WHERE entity_type = 'book_format' LIMIT :limit"
    ), {"limit": max_per_domain}).fetchall()
    for pid in [r[0] for r in prob_rows2][:max_per_domain // 10]:
        for fid in [r[0] for r in fmt_rows][:3]:
            key = (pid, fid, "suitable_format")
            if key in existing:
                skipped += 1
                continue
            relation = DiscoveryEntityRelation(
                source_entity_id=pid,
                target_entity_id=fid,
                relation_type="suitable_format",
                weight=1.0,
                confidence=0.50,
                evidence_source="type_cross:problem_format",
            )
            db.add(relation)
            existing.add(key)
            result_relations.append(relation)
            created += 1
            co_occurrence_count += 1

    if created:
        db.commit()
        for rel in result_relations:
            db.refresh(rel)

    return RelationBuilderResult(
        created=created,
        skipped=skipped,
        co_occurrence=co_occurrence_count,
        dict_pairs=dict_pair_count,
        domain_relations=domain_relations_count,
        relations=result_relations,
    )
