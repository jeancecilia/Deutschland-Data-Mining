from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.keyword import Keyword
from app.models.run import SearchResult, SearchRun
from app.schemas.search import SearchResultItemRead, SearchRunDetailRead
from app.services.amazon_search import (
    AmazonBlockedError,
    AmazonFetchError,
    AmazonSearchListing,
    AmazonTransientError,
    collect_search_results,
)


def collect_and_store_search_run(db: Session, keyword: Keyword) -> SearchRunDetailRead:
    search_run = SearchRun(
        keyword_id=keyword.id,
        marketplace=keyword.marketplace,
        run_at=datetime.now(UTC),
        source_type="amazon_search",
        status="pending",
    )
    db.add(search_run)
    db.commit()
    db.refresh(search_run)

    try:
        listings = collect_search_results(keyword.keyword)
        search_run.status = "running"
        db.add(search_run)
        db.flush()
        result_items: list[SearchResultItemRead] = []

        for position, listing in enumerate(listings, start=1):
            book = _get_or_create_book(db, listing, keyword.marketplace)
            db.add(
                SearchResult(
                    search_run_id=search_run.id,
                    book_id=book.id,
                    position=position,
                    is_sponsored=listing.is_sponsored,
                    price=listing.price,
                    rating=listing.rating,
                    review_count=listing.review_count,
                    captured_at=listing.captured_at,
                )
            )
            result_items.append(
                SearchResultItemRead(
                    asin=listing.asin,
                    title=book.title,
                    marketplace=book.marketplace,
                    position=position,
                    is_sponsored=listing.is_sponsored,
                    price=listing.price,
                    rating=listing.rating,
                    review_count=listing.review_count,
                    captured_at=listing.captured_at,
                )
            )

        search_run.status = "completed"
        search_run.result_count = len(result_items)
        if not result_items:
            search_run.notes = "No parsable Amazon search listings found."
        db.commit()
        db.refresh(search_run)

        return SearchRunDetailRead(
            id=search_run.id,
            keyword_id=search_run.keyword_id,
            marketplace=search_run.marketplace,
            run_at=search_run.run_at,
            source_type=search_run.source_type,
            status=search_run.status,
            result_count=search_run.result_count,
            notes=search_run.notes,
            results=result_items,
        )
    except AmazonBlockedError as exc:
        db.rollback()
        failed_run = db.get(SearchRun, search_run.id)
        if failed_run is not None:
            failed_run.status = "blocked"
            failed_run.notes = str(exc)
            db.add(failed_run)
            db.commit()
        raise
    except AmazonTransientError as exc:
        db.rollback()
        failed_run = db.get(SearchRun, search_run.id)
        if failed_run is not None:
            failed_run.status = "fetch_failed"
            failed_run.notes = str(exc)
            db.add(failed_run)
            db.commit()
        raise
    except AmazonFetchError as exc:
        db.rollback()
        failed_run = db.get(SearchRun, search_run.id)
        if failed_run is not None:
            failed_run.status = "fetch_failed"
            failed_run.notes = str(exc)
            db.add(failed_run)
            db.commit()
        raise
    except Exception as exc:
        db.rollback()
        failed_run = db.get(SearchRun, search_run.id)
        if failed_run is not None:
            failed_run.status = "failed"
            failed_run.notes = str(exc)
            db.add(failed_run)
            db.commit()
        raise


def _get_or_create_book(db: Session, listing: AmazonSearchListing, marketplace: str) -> Book:
    statement = select(Book).where(Book.asin == listing.asin)
    book = db.scalars(statement).one_or_none()
    if book is None:
        book = Book(
            asin=listing.asin,
            title=listing.title,
            marketplace=marketplace,
        )
        db.add(book)
        db.flush()
        return book

    if listing.title and not book.title:
        book.title = listing.title
    if marketplace and not book.marketplace:
        book.marketplace = marketplace
    db.flush()
    return book


def list_search_runs_for_keyword(db: Session, keyword_id: int) -> list[SearchRunDetailRead]:
    statement = (
        select(SearchRun)
        .where(SearchRun.keyword_id == keyword_id)
        .order_by(SearchRun.run_at.desc())
    )
    runs = list(db.scalars(statement))
    payload: list[SearchRunDetailRead] = []

    for run in runs:
        results_statement = (
            select(SearchResult, Book)
            .join(Book, SearchResult.book_id == Book.id)
            .where(SearchResult.search_run_id == run.id)
            .order_by(SearchResult.position.asc())
        )
        results = [
            SearchResultItemRead(
                asin=book.asin,
                title=book.title,
                marketplace=book.marketplace,
                position=result.position,
                is_sponsored=result.is_sponsored,
                price=result.price,
                rating=result.rating,
                review_count=result.review_count,
                captured_at=result.captured_at,
            )
            for result, book in db.execute(results_statement).all()
        ]
        payload.append(
            SearchRunDetailRead(
                id=run.id,
                keyword_id=run.keyword_id,
                marketplace=run.marketplace,
                run_at=run.run_at,
                source_type=run.source_type,
                status=run.status,
                result_count=run.result_count,
                notes=run.notes,
                results=results,
            )
        )

    return payload


def refresh_recent_keyword_search_runs(
    db: Session,
    *,
    keyword_limit: int = 6,
    min_hours_between_runs: int = 24,
) -> dict[str, int]:
    keyword_pool = list(
        db.scalars(
            select(Keyword)
            .where(Keyword.status != "ignored")
            .order_by(Keyword.priority.desc(), Keyword.updated_at.desc(), Keyword.id.asc())
            .limit(max(12, keyword_limit * 3))
        )
    )
    keywords = [
        keyword
        for keyword in keyword_pool
        if keyword.seed_keyword_id is None or keyword.priority >= 80
    ][:keyword_limit]

    processed_keywords = 0
    refreshed_runs = 0
    skipped_keywords = 0
    failed_keywords = 0
    now = datetime.now(UTC)

    for keyword in keywords:
        processed_keywords += 1
        latest_run = db.scalars(
            select(SearchRun)
            .where(SearchRun.keyword_id == keyword.id)
            .order_by(SearchRun.run_at.desc(), SearchRun.id.desc())
        ).first()
        if latest_run is not None:
            latest_run_at = latest_run.run_at
            if latest_run_at.tzinfo is None:
                latest_run_at = latest_run_at.replace(tzinfo=UTC)
            if now - latest_run_at < timedelta(hours=min_hours_between_runs):
                skipped_keywords += 1
                continue

        try:
            collect_and_store_search_run(db, keyword)
            refreshed_runs += 1
        except Exception:
            failed_keywords += 1

    return {
        "processed_keywords": processed_keywords,
        "refreshed_runs": refreshed_runs,
        "skipped_keywords": skipped_keywords,
        "failed_keywords": failed_keywords,
    }
