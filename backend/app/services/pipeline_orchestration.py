from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.keyword import Keyword
from app.models.run import BSRSnapshot
from app.models.run import SearchResult, SearchRun
from app.schemas.book import BSRSnapshotRead, BookDetailCollectionRead, BookRead
from app.schemas.pipeline import PipelineRunRead
from app.services.book_collection import collect_and_store_book_details
from app.services.keyword_expansion import expand_keyword
from app.services.keyword_intelligence import infer_keyword_intelligence
from app.services.niche_cluster_analysis import build_and_analyze_seed_cluster
from app.services.review_collection import collect_and_store_reviews
from app.services.review_intelligence import analyze_book_reviews
from app.services.review_intelligence import list_review_clusters_for_book
from app.services.search_collection import collect_and_store_search_run, list_search_runs_for_keyword


def run_seed_pipeline(
    db: Session,
    seed_keyword: Keyword,
    *,
    collect_related_limit: int = 8,
    enrich_top_books: int = 6,
    review_page: int = 1,
    reuse_existing_runs: bool = True,
    collect_details: bool = False,
    collect_reviews: bool = False,
) -> PipelineRunRead:
    expansions = expand_keyword(seed_keyword.keyword)
    _store_expansions(db, seed_keyword, expansions)

    related_keywords = list(
        db.scalars(
            select(Keyword)
            .where((Keyword.id == seed_keyword.id) | (Keyword.seed_keyword_id == seed_keyword.id))
            .order_by(Keyword.id.asc())
        )
    )

    from datetime import UTC, datetime, timedelta
    SEARCH_RUN_MAX_AGE_HOURS = 24

    keywords_to_collect = related_keywords[: max(1, collect_related_limit)]
    collected_search_runs = []
    for keyword in keywords_to_collect:
        if reuse_existing_runs:
            existing_runs = list_search_runs_for_keyword(db, keyword.id)
            for run in existing_runs:
                age = datetime.now(UTC) - run.run_at
                if age < timedelta(hours=SEARCH_RUN_MAX_AGE_HOURS):
                    collected_search_runs.append(run)
                    break
            if collected_search_runs and collected_search_runs[-1].keyword_id == keyword.id:
                continue

        try:
            collected_search_runs.append(collect_and_store_search_run(db, keyword))
        except Exception:
            existing_runs = list_search_runs_for_keyword(db, keyword.id)
            if existing_runs:
                collected_search_runs.append(existing_runs[0])
            else:
                raise

    selected_run_ids = [run.id for run in db.scalars(
        select(SearchRun)
        .where(SearchRun.keyword_id.in_([keyword.id for keyword in keywords_to_collect]), SearchRun.status == "completed")
        .order_by(SearchRun.run_at.desc())
    )]

    book_ids = [
        result.book_id
        for result in db.scalars(
            select(SearchResult)
            .where(SearchResult.search_run_id.in_(selected_run_ids))
            .order_by(SearchResult.position.asc())
            .limit(max(1, enrich_top_books))
        )
    ]
    unique_book_ids: list[int] = []
    seen: set[int] = set()
    for book_id in book_ids:
        if book_id in seen:
            continue
        seen.add(book_id)
        unique_book_ids.append(book_id)

    enriched_books = []
    analyzed_review_books: dict[int, list] = {}
    if collect_details or collect_reviews:
        for book_id in unique_book_ids:
            book = db.get(Book, book_id)
            if book is None:
                continue
            if collect_details:
                try:
                    enriched_books.append(collect_and_store_book_details(db, book))
                except Exception:
                    enriched_books.append(_build_book_detail_fallback(db, book))

            if collect_reviews:
                try:
                    collect_and_store_reviews(db, book, page=review_page)
                except Exception:
                    pass

                try:
                    analyzed_review_books[book.id] = analyze_book_reviews(db, book)
                except Exception:
                    analyzed_review_books[book.id] = list_review_clusters_for_book(db, book.id)

    cluster_analysis = build_and_analyze_seed_cluster(db, seed_keyword)

    return PipelineRunRead(
        seed_keyword_id=seed_keyword.id,
        seed_keyword=seed_keyword.keyword,
        expanded_keyword_count=len(related_keywords),
        collected_search_runs=collected_search_runs,
        enriched_books=enriched_books,
        analyzed_review_books=analyzed_review_books,
        cluster_analysis=cluster_analysis,
    )


def _store_expansions(db: Session, seed_keyword: Keyword, expansions: list[object]) -> None:
    existing = {
        keyword.keyword.casefold()
        for keyword in db.scalars(select(Keyword).where(Keyword.seed_keyword_id == seed_keyword.id))
    }
    for expansion in expansions:
        expansion_keyword = getattr(expansion, "keyword")
        expansion_type = getattr(expansion, "keyword_type")
        if expansion_keyword.casefold() in existing:
            continue
        intelligence = infer_keyword_intelligence(expansion_keyword, book_type=seed_keyword.book_type)
        db.add(
            Keyword(
                keyword=expansion_keyword,
                language=seed_keyword.language,
                marketplace=seed_keyword.marketplace,
                seed_keyword_id=seed_keyword.id,
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
                book_type=seed_keyword.book_type,
                risk_level=seed_keyword.risk_level or intelligence.risk_level,
            )
        )
    db.commit()


def _build_book_detail_fallback(db: Session, book: Book) -> BookDetailCollectionRead:
    snapshot = db.scalars(
        select(BSRSnapshot)
        .where(BSRSnapshot.book_id == book.id)
        .order_by(BSRSnapshot.captured_at.desc(), BSRSnapshot.id.desc())
    ).first()
    return BookDetailCollectionRead(
        book=BookRead.model_validate(book),
        latest_bsr_snapshot=BSRSnapshotRead.model_validate(snapshot) if snapshot else None,
    )
