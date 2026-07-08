from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.keyword import Keyword
from app.schemas.analysis import OpportunityAnalysisRead
from app.schemas.analysis import NicheClusterAnalysisRead
from app.schemas.keyword import (
    KeywordCreate,
    KeywordExpansionRead,
    KeywordExpansionResponse,
    KeywordRead,
    KeywordUpdate,
)
from app.schemas.pipeline import PipelineRunRead
from app.schemas.search import SearchRunDetailRead
from app.services.amazon_search import AmazonFetchError
from app.services.keyword_expansion import expand_keyword
from app.services.keyword_intelligence import infer_keyword_intelligence
from app.services.niche_cluster_analysis import build_and_analyze_seed_cluster
from app.services.opportunity_analysis import analyze_keyword_opportunity
from app.services.pipeline_orchestration import run_seed_pipeline
from app.services.search_collection import collect_and_store_search_run, list_search_runs_for_keyword


router = APIRouter()


@router.get("", response_model=list[KeywordRead])
def list_keywords(db: Session = Depends(get_db)) -> list[Keyword]:
    statement = select(Keyword).order_by(Keyword.priority.desc(), Keyword.updated_at.desc(), Keyword.id.desc())
    return list(db.scalars(statement))


@router.post("", response_model=KeywordRead, status_code=status.HTTP_201_CREATED)
def create_keyword(payload: KeywordCreate, db: Session = Depends(get_db)) -> Keyword:
    values = payload.model_dump()
    intelligence = infer_keyword_intelligence(values["keyword"], book_type=values.get("book_type"))
    keyword = Keyword(
        **values,
        target_audience=values.get("target_audience") or intelligence.target_audience,
        category_hint=values.get("category_hint") or intelligence.category_hint,
        search_intent_family=intelligence.search_intent_family,
        specificity_score=intelligence.specificity_score,
        intent_score=intelligence.intent_score,
        audience_clarity_score=intelligence.audience_clarity_score,
        format_suitability_score=intelligence.format_suitability_score,
        competition_probability_score=intelligence.competition_probability_score,
        production_effort_score=intelligence.production_effort_score,
        risk_level=values.get("risk_level") or intelligence.risk_level,
    )
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.patch("/{keyword_id}", response_model=KeywordRead)
def update_keyword(
    keyword_id: int,
    payload: KeywordUpdate,
    db: Session = Depends(get_db),
) -> Keyword:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(keyword, field_name, value)

    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.post("/{keyword_id}/expand", response_model=list[KeywordExpansionRead])
def expand_seed_keyword(keyword_id: int, db: Session = Depends(get_db)) -> list[KeywordExpansionRead]:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return [
        KeywordExpansionRead(keyword=expansion.keyword, keyword_type=expansion.keyword_type)
        for expansion in expand_keyword(keyword.keyword)
    ]


@router.post("/{keyword_id}/expand-and-store", response_model=KeywordExpansionResponse)
def expand_seed_keyword_and_store(
    keyword_id: int, db: Session = Depends(get_db)
) -> KeywordExpansionResponse:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    expansions = expand_keyword(keyword.keyword)
    _store_keyword_expansions(db, keyword, expansions)
    return KeywordExpansionResponse(
        seed_keyword_id=keyword.id,
        seed_keyword=keyword.keyword,
        expansions=[
            KeywordExpansionRead(keyword=expansion.keyword, keyword_type=expansion.keyword_type)
            for expansion in expansions
        ],
    )


@router.post("/{keyword_id}/collect-search", response_model=SearchRunDetailRead)
def collect_search_for_keyword(
    keyword_id: int, db: Session = Depends(get_db)
) -> SearchRunDetailRead:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    try:
        return collect_and_store_search_run(db, keyword)
    except AmazonFetchError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{keyword_id}/search-runs", response_model=list[SearchRunDetailRead])
def list_keyword_search_runs(
    keyword_id: int, db: Session = Depends(get_db)
) -> list[SearchRunDetailRead]:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return list_search_runs_for_keyword(db, keyword_id)


@router.post("/{keyword_id}/analyze-opportunity", response_model=OpportunityAnalysisRead)
def analyze_keyword(
    keyword_id: int, db: Session = Depends(get_db)
) -> OpportunityAnalysisRead:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    try:
        return analyze_keyword_opportunity(db, keyword)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{keyword_id}/analyze-cluster", response_model=NicheClusterAnalysisRead)
def analyze_keyword_cluster(
    keyword_id: int, db: Session = Depends(get_db)
) -> NicheClusterAnalysisRead:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    seed_keyword = keyword
    if keyword.seed_keyword_id is not None:
        parent_keyword = db.get(Keyword, keyword.seed_keyword_id)
        if parent_keyword is not None:
            seed_keyword = parent_keyword

    try:
        return build_and_analyze_seed_cluster(db, seed_keyword)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{keyword_id}/run-pipeline", response_model=PipelineRunRead)
def run_keyword_pipeline(
    keyword_id: int,
    collect_related_limit: int = 8,
    enrich_top_books: int = 6,
    review_page: int = 1,
    reuse_existing_runs: bool = True,
    collect_details: bool = False,
    collect_reviews: bool = False,
    db: Session = Depends(get_db),
) -> PipelineRunRead:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    seed_keyword = keyword
    if keyword.seed_keyword_id is not None:
        parent_keyword = db.get(Keyword, keyword.seed_keyword_id)
        if parent_keyword is not None:
            seed_keyword = parent_keyword

    try:
        return run_seed_pipeline(
            db,
            seed_keyword,
            collect_related_limit=collect_related_limit,
            enrich_top_books=enrich_top_books,
            review_page=review_page,
            reuse_existing_runs=reuse_existing_runs,
            collect_details=collect_details,
            collect_reviews=collect_reviews,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _store_keyword_expansions(db: Session, keyword: Keyword, expansions: list[object]) -> None:
    existing_keywords = {
        item.keyword.casefold(): item
        for item in db.scalars(select(Keyword).where(Keyword.seed_keyword_id == keyword.id))
    }

    for expansion in expansions:
        expansion_keyword = getattr(expansion, "keyword")
        expansion_type = getattr(expansion, "keyword_type")
        if expansion_keyword.casefold() in existing_keywords:
            continue
        intelligence = infer_keyword_intelligence(expansion_keyword, book_type=keyword.book_type)
        db.add(
            Keyword(
                keyword=expansion_keyword,
                language=keyword.language,
                marketplace=keyword.marketplace,
                seed_keyword_id=keyword.id,
                keyword_type=expansion_type,
                target_audience=intelligence.target_audience,
                category_hint=intelligence.category_hint,
                search_intent_family=intelligence.search_intent_family,
                specificity_score=intelligence.specificity_score,
                intent_score=intelligence.intent_score,
                audience_clarity_score=intelligence.audience_clarity_score,
                format_suitability_score=intelligence.format_suitability_score,
                competition_probability_score=intelligence.competition_probability_score,
                production_effort_score=intelligence.production_effort_score,
                status="expanded",
                book_type=keyword.book_type,
                risk_level=keyword.risk_level or intelligence.risk_level,
            )
        )

    db.commit()
