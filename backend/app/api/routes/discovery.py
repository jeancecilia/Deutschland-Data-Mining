from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.discovery import (
    DiscoveryCandidateRead,
    DiscoveryCycleRead,
    DiscoveryGenerateRead,
    DiscoveryUniverseRead,
)
from app.services.discovery_engine import (
    generate_discovery_candidates,
    get_discovery_candidate,
    list_discovery_candidates,
    list_discovery_universe,
    run_discovery_cycle,
    validate_discovery_candidate,
)


router = APIRouter()


@router.get("/universe", response_model=DiscoveryUniverseRead)
def get_discovery_universe(db: Session = Depends(get_db)) -> DiscoveryUniverseRead:
    return list_discovery_universe(db)


@router.get("/candidates", response_model=list[DiscoveryCandidateRead])
def get_discovery_candidates(
    status: str | None = Query(default=None),
    limit: int = Query(default=40, ge=1, le=250),
    db: Session = Depends(get_db),
) -> list[DiscoveryCandidateRead]:
    return list_discovery_candidates(db, limit=limit, status=status)


@router.get("/candidates/{candidate_id}", response_model=DiscoveryCandidateRead)
def get_discovery_candidate_route(
    candidate_id: int,
    db: Session = Depends(get_db),
) -> DiscoveryCandidateRead:
    try:
        return get_discovery_candidate(db, candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/generate", response_model=DiscoveryGenerateRead)
def generate_discovery_candidates_route(
    limit: int = Query(default=120, ge=10, le=500),
    db: Session = Depends(get_db),
) -> DiscoveryGenerateRead:
    return generate_discovery_candidates(db, limit=limit)


@router.post("/run-cycle", response_model=DiscoveryCycleRead)
def run_discovery_cycle_route(
    generate_limit: int = Query(default=120, ge=10, le=500),
    validate_limit: int = Query(default=6, ge=1, le=20),
    auto_generate_reports: bool = Query(default=True),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> DiscoveryCycleRead:
    return run_discovery_cycle(
        db,
        generate_limit=generate_limit,
        validate_limit=validate_limit,
        auto_generate_reports=auto_generate_reports,
        force=force,
    )


@router.post("/candidates/{candidate_id}/validate", response_model=DiscoveryCandidateRead)
def validate_discovery_candidate_route(
    candidate_id: int,
    auto_generate_reports: bool = Query(default=False),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> DiscoveryCandidateRead:
    try:
        return validate_discovery_candidate(
            db,
            candidate_id,
            auto_generate_reports=auto_generate_reports,
            force=force,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
