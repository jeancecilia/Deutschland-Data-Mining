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
    from sqlalchemy import func, select

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

    return DiscoveryOverviewRead(
        source_count=source_count,
        active_source_count=active_source_count,
        raw_item_count=raw_item_count,
        unprocessed_raw_count=unprocessed_raw_count,
        entity_count=entity_count,
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
    limit_per_rule: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    from app.services.discovery.relation_builder import build_entity_relations
    result = build_entity_relations(db, limit_per_rule=limit_per_rule)
    return {"created": result.created, "skipped": result.skipped}


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
    promoted = sum(1 for r in results if r.recommended_action == "promote_to_seed")
    rejected = sum(1 for r in results if r.recommended_action == "reject")
    manual = sum(1 for r in results if r.recommended_action == "manual_review")
    return {
        "total": len(results),
        "promoted": promoted,
        "rejected": rejected,
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


@router.post("/candidates/promote")
def promote_candidates(
    limit: int = Query(default=50, ge=1, le=200),
    min_score: int = Query(default=50, ge=0, le=100),
    db: Session = Depends(get_db),
) -> dict:
    batch = promote_candidates_to_seeds(db, limit=limit, min_score=min_score)
    return {
        "promoted": batch.promoted,
        "skipped": batch.skipped,
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
