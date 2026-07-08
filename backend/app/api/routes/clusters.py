from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.niche import NicheCluster, OpportunityScore
from app.schemas.analysis import NicheClusterAnalysisRead
from app.schemas.book import ClusterBSRRefreshRead
from app.schemas.sachbuch import SachbuchAnalysisRead
from app.services.bsr_tracking import collect_cluster_bsr_snapshots
from app.services.niche_cluster_analysis import get_cluster_analysis
from app.services.sachbuch_analysis import analyze_sachbuch_cluster, get_latest_sachbuch_analysis


router = APIRouter()


@router.get("")
def list_clusters(db: Session = Depends(get_db)) -> list[dict]:
    clusters = list(
        db.scalars(select(NicheCluster).order_by(NicheCluster.updated_at.desc(), NicheCluster.id.desc()))
    )
    payload: list[dict] = []
    for cluster in clusters:
        latest_score = db.scalars(
            select(OpportunityScore)
            .where(OpportunityScore.niche_cluster_id == cluster.id)
            .order_by(OpportunityScore.created_at.desc())
        ).first()
        payload.append(
            {
                "id": cluster.id,
                "name": cluster.name,
                "main_keyword": cluster.main_keyword,
                "book_class": cluster.book_class,
                "status": cluster.status,
                "latest_final_score": latest_score.final_score if latest_score else None,
            }
        )
    return payload


@router.get("/{cluster_id}", response_model=NicheClusterAnalysisRead)
def get_cluster(cluster_id: int, db: Session = Depends(get_db)) -> NicheClusterAnalysisRead:
    try:
        return get_cluster_analysis(db, cluster_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{cluster_id}/analyze-sachbuch", response_model=SachbuchAnalysisRead)
def analyze_cluster_sachbuch(cluster_id: int, db: Session = Depends(get_db)) -> SachbuchAnalysisRead:
    try:
        return analyze_sachbuch_cluster(db, cluster_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{cluster_id}/sachbuch", response_model=SachbuchAnalysisRead)
def get_cluster_sachbuch(cluster_id: int, db: Session = Depends(get_db)) -> SachbuchAnalysisRead:
    try:
        return get_latest_sachbuch_analysis(db, cluster_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{cluster_id}/collect-bsr-snapshots", response_model=ClusterBSRRefreshRead)
def collect_cluster_bsr_snapshots_route(
    cluster_id: int,
    limit: int = Query(default=5, ge=1, le=25),
    min_hours_between_snapshots: int = Query(default=12, ge=1, le=168),
    db: Session = Depends(get_db),
) -> ClusterBSRRefreshRead:
    try:
        return collect_cluster_bsr_snapshots(
            db,
            cluster_id,
            limit=limit,
            min_hours_between_snapshots=min_hours_between_snapshots,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
