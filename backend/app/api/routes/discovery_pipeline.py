"""API routes for the Initial Discovery Pipeline."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.discovery_pipeline import (
    DiscoveryEntityRead,
    DiscoveryEntityRelationCreate,
    DiscoveryEntityRelationRead,
    DiscoveryOverviewRead,
    DiscoverySourceCreate,
    DiscoverySourceRead,
    DiscoverySourceUpdate,
    NicheCandidateKeywordRead,
    NicheCandidateRead,
    NicheCandidateUpdate,
    RawDiscoveryItemRead,
)
from app.services.discovery import (
    compose_niche_candidates,
    ensure_default_discovery_sources,
    extract_entities_from_raw_items,
    get_entities_by_type,
    get_entity_graph_overview,
    get_graph_neighbors,
    import_all_seed_universes,
    list_discovery_sources,
    promote_candidates_to_seeds,
    validate_candidates_fast,
)

router = APIRouter()


# ── Overview ────────────────────────────────────────────────────────────────


@router.get("/overview", response_model=DiscoveryOverviewRead)
def get_discovery_overview(db: Session = Depends(get_db)) -> DiscoveryOverviewRead:
    """Return counts for the entire discovery pipeline (uses SQL COUNT)."""
    from app.models.discovery_pipeline import (
        DiscoverySource,
        RawDiscoveryItem,
        DiscoveryEntity,
        DiscoveryEntityRelation,
        NicheCandidate,
    )
    from sqlalchemy import func, select, text

    source_count = db.scalar(select(func.count(DiscoverySource.id))) or 0
    active_source_count = db.scalar(
        select(func.count(DiscoverySource.id)).where(DiscoverySource.is_active == True)  # noqa: E712
    ) or 0
    raw_item_count = db.scalar(select(func.count(RawDiscoveryItem.id))) or 0
    unprocessed_raw_count = db.scalar(
        select(func.count(RawDiscoveryItem.id)).where(RawDiscoveryItem.status == "new")
    ) or 0
    entity_count = db.scalar(select(func.count(DiscoveryEntity.id))) or 0
    relation_count = db.scalar(select(func.count(DiscoveryEntityRelation.id))) or 0
    candidate_count = db.scalar(select(func.count(NicheCandidate.id))) or 0
    new_candidate_count = db.scalar(
        select(func.count(NicheCandidate.id)).where(NicheCandidate.status == "new")
    ) or 0
    promoted_candidate_count = db.scalar(
        select(func.count(NicheCandidate.id)).where(NicheCandidate.status == "promoted_to_seed")
    ) or 0
    rejected_candidate_count = db.scalar(
        select(func.count(NicheCandidate.id)).where(NicheCandidate.status == "rejected")
    ) or 0

    # Entity type breakdown
    entity_types: dict[str, int] = {}
    type_rows = db.execute(
        text("SELECT entity_type, COUNT(*) FROM discovery_entities GROUP BY entity_type ORDER BY COUNT(*) DESC")
    ).all()
    for row in type_rows:
        entity_types[str(row[0])] = int(row[1])

    # Domain stats (from raw items)
    domain_count = db.scalar(
        text("SELECT COUNT(DISTINCT metadata_json->>'domain') FROM raw_discovery_items WHERE metadata_json->>'domain' IS NOT NULL")
    ) or 0

    # Domain stats (from entities)
    entity_domain_count = db.scalar(
        text("SELECT COUNT(DISTINCT metadata_json->>'domain') FROM discovery_entities WHERE metadata_json->>'domain' IS NOT NULL AND metadata_json->>'domain' != ''")
    ) or 0

    top_domains: list[dict[str, object]] = []
    domain_rows = db.execute(
        text("SELECT metadata_json->>'domain' as domain, COUNT(*) as cnt FROM raw_discovery_items WHERE metadata_json->>'domain' IS NOT NULL GROUP BY domain ORDER BY cnt DESC LIMIT 10")
    ).all()
    for row in domain_rows:
        top_domains.append({"domain": str(row[0]), "count": int(row[1])})

    return DiscoveryOverviewRead(
        source_count=source_count,
        active_source_count=active_source_count,
        raw_item_count=raw_item_count,
        unprocessed_raw_count=unprocessed_raw_count,
        entity_count=entity_count,
        entity_types=entity_types,
        domain_count=domain_count,
        entity_domain_count=entity_domain_count,
        top_domains=top_domains,
        relation_count=relation_count,
        candidate_count=candidate_count,
        new_candidate_count=new_candidate_count,
        promoted_candidate_count=promoted_candidate_count,
        rejected_candidate_count=rejected_candidate_count,
    )


# ── Sources ─────────────────────────────────────────────────────────────────


@router.get("/sources", response_model=list[DiscoverySourceRead])
def get_sources(db: Session = Depends(get_db)) -> list[DiscoverySourceRead]:
    return [DiscoverySourceRead.model_validate(s) for s in list_discovery_sources(db)]


@router.post("/sources", response_model=DiscoverySourceRead)
def create_source(
    payload: DiscoverySourceCreate,
    db: Session = Depends(get_db),
) -> DiscoverySourceRead:
    from app.models.discovery_pipeline import DiscoverySource
    source = DiscoverySource(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return DiscoverySourceRead.model_validate(source)


@router.patch("/sources/{source_id}", response_model=DiscoverySourceRead)
def update_source(
    source_id: int,
    payload: DiscoverySourceUpdate,
    db: Session = Depends(get_db),
) -> DiscoverySourceRead:
    from app.models.discovery_pipeline import DiscoverySource
    source = db.get(DiscoverySource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    db.add(source)
    db.commit()
    db.refresh(source)
    return DiscoverySourceRead.model_validate(source)


# ── Seed Import ─────────────────────────────────────────────────────────────


@router.post("/import-seeds")
def import_seed_data(db: Session = Depends(get_db)) -> dict:
    """Import all CSV seed universe files into raw_discovery_items."""
    results = import_all_seed_universes(db)
    return {"status": "ok", "imported": results}


# ── Entities ────────────────────────────────────────────────────────────────


@router.get("/entities", response_model=list[DiscoveryEntityRead])
def get_entities(
    entity_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[DiscoveryEntityRead]:
    return [DiscoveryEntityRead.model_validate(e) for e in get_entities_by_type(db, entity_type)]


@router.post("/entities/extract")
def extract_entities(
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> dict:
    """Extract entities from raw_discovery_items."""
    result = extract_entities_from_raw_items(db, limit=limit)
    return {
        "created": result.created,
        "updated": result.updated,
        "skipped": result.skipped,
    }


# ── Relations (Topic Graph) ─────────────────────────────────────────────────


@router.get("/graph", response_model=dict)
def get_graph_overview(db: Session = Depends(get_db)) -> dict:
    overview = get_entity_graph_overview(db)
    return {
        "entity_count": overview.entity_count,
        "relation_count": overview.relation_count,
        "entity_types": overview.entity_types,
    }


@router.get("/graph/{entity_id}/neighbors")
def get_entity_neighbors(
    entity_id: int,
    relation_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    return get_graph_neighbors(db, entity_id, relation_type=relation_type)


@router.post("/relations/build")
def build_relations(
    limit_per_rule: int = Query(default=20, ge=1, le=500),
    max_domains: int = Query(default=1000, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> dict:
    from app.services.discovery.relation_builder import build_entity_relations
    result = build_entity_relations(db, limit_per_rule=limit_per_rule, max_domains=max_domains)
    return {
        "created": result.created,
        "skipped": result.skipped,
        "domain_relations": getattr(result, 'domain_relations', 0),
        "dict_pairs": result.dict_pairs,
    }


# ── Niche Candidates ────────────────────────────────────────────────────────


@router.get("/candidates", response_model=list[NicheCandidateRead])
def get_niche_candidates(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[NicheCandidateRead]:
    from app.models.discovery_pipeline import NicheCandidate, DiscoveryEntity
    from sqlalchemy import select

    stmt = select(NicheCandidate)
    if status:
        stmt = stmt.where(NicheCandidate.status == status)
    stmt = stmt.order_by(NicheCandidate.fast_validation_score.desc().nullslast()).limit(limit)
    candidates = list(db.scalars(stmt))

    # Resolve entity names
    entity_ids: set[int] = set()
    for c in candidates:
        if c.main_topic_entity_id:
            entity_ids.add(c.main_topic_entity_id)
        if c.audience_entity_id:
            entity_ids.add(c.audience_entity_id)
        if c.problem_entity_id:
            entity_ids.add(c.problem_entity_id)
        if c.format_entity_id:
            entity_ids.add(c.format_entity_id)
    entity_map = {
        e.id: e.name
        for e in db.scalars(select(DiscoveryEntity).where(DiscoveryEntity.id.in_(entity_ids)))
    } if entity_ids else {}

    result = []
    for c in candidates:
        read = NicheCandidateRead.model_validate(c)
        read.main_topic = entity_map.get(c.main_topic_entity_id) if c.main_topic_entity_id else None
        read.audience = entity_map.get(c.audience_entity_id) if c.audience_entity_id else None
        read.problem = entity_map.get(c.problem_entity_id) if c.problem_entity_id else None
        read.format = entity_map.get(c.format_entity_id) if c.format_entity_id else None
        result.append(read)
    return result


@router.post("/candidates/compose")
def compose_candidates(
    limit: int = Query(default=500, ge=10, le=5000),
    db: Session = Depends(get_db),
) -> dict:
    batch = compose_niche_candidates(db, limit=limit)
    return {
        "created": batch.created,
        "skipped_no_relation": batch.skipped_no_relation,
        "skipped_blocked": batch.skipped_blocked,
        "skipped_duplicate": batch.skipped_duplicate,
        "skipped_generic": batch.skipped_generic,
    }


@router.post("/candidates/validate")
def fast_validate(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    results = validate_candidates_fast(db, limit=limit)
    go_count = sum(1 for r in results if r.recommendation_label == "GO")
    blocked = sum(1 for r in results if r.recommendation_label in ("NO-GO", "BLOCKED"))
    manual = sum(1 for r in results if r.recommendation_label in ("REVIEW_REQUIRED", "HIGH_RISK_OPPORTUNITY", "MAYBE"))
    return {
        "total": len(results),
        "go": go_count,
        "blocked": blocked,
        "manual_review": manual,
    }


@router.patch("/candidates/{candidate_id}", response_model=NicheCandidateRead)
def update_candidate(
    candidate_id: int,
    payload: NicheCandidateUpdate,
    db: Session = Depends(get_db),
) -> NicheCandidateRead:
    from app.models.discovery_pipeline import NicheCandidate
    candidate = db.get(NicheCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(candidate, key, value)
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return NicheCandidateRead.model_validate(candidate)


@router.post("/candidates/{candidate_id}/approve")
def approve_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Approve a candidate for promotion (manual review gate)."""
    from app.models.discovery_pipeline import NicheCandidate
    candidate = db.get(NicheCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.status = "approved_for_promotion"
    candidate.promotion_reason = "Manually approved"
    db.add(candidate)
    db.commit()
    return {"status": "ok", "candidate_id": candidate_id, "new_status": "approved_for_promotion"}


@router.post("/candidates/{candidate_id}/reject")
def reject_candidate(
    candidate_id: int,
    reason: str = Query(default="Manually rejected"),
    db: Session = Depends(get_db),
) -> dict:
    """Reject a candidate."""
    from app.models.discovery_pipeline import NicheCandidate
    candidate = db.get(NicheCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.status = "rejected"
    candidate.rejection_reason = reason
    db.add(candidate)
    db.commit()
    return {"status": "ok", "candidate_id": candidate_id, "new_status": "rejected"}


@router.post("/candidates/promote")
def promote_candidates(
    limit: int = Query(default=50, ge=1, le=200),
    min_score: int = Query(default=50, ge=0, le=100),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> dict:
    batch = promote_candidates_to_seeds(db, limit=limit, min_score=min_score, force=force)
    return {
        "promoted": batch.promoted,
        "skipped": batch.skipped,
        "skipped_auto_blocked": batch.skipped_auto_blocked,
        "skipped_risk": batch.skipped_risk,
        "keyword_ids": [kw.id for kw in batch.keywords],
    }


# ── Candidate Keywords ──────────────────────────────────────────────────────


@router.get("/candidates/{candidate_id}/keywords", response_model=list[NicheCandidateKeywordRead])
def get_candidate_keywords(
    candidate_id: int,
    db: Session = Depends(get_db),
) -> list[NicheCandidateKeywordRead]:
    from app.models.discovery_pipeline import NicheCandidateKeyword
    from sqlalchemy import select
    keywords = list(
        db.scalars(
            select(NicheCandidateKeyword)
            .where(NicheCandidateKeyword.niche_candidate_id == candidate_id)
            .order_by(NicheCandidateKeyword.confidence.desc())
        )
    )
    return [NicheCandidateKeywordRead.model_validate(kw) for kw in keywords]
