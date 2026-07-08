from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ai import BookInsight
from app.models.book import Book
from app.models.review import Review
from app.schemas.ai import BookInsightRead
from app.schemas.book import BookBSRHistoryRead, BookDetailCollectionRead, BookRead
from app.schemas.review_cluster import ReviewClusterRead
from app.schemas.review import ReviewRead
from app.services.ai_intelligence import upsert_book_insight
from app.services.bsr_tracking import get_book_bsr_history
from app.services.book_collection import collect_and_store_book_details, list_books
from app.services.review_collection import collect_and_store_reviews
from app.services.review_intelligence import analyze_book_reviews, list_review_clusters_for_book


router = APIRouter()


@router.get("", response_model=list[BookRead])
def list_books_route(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Book]:
    return list_books(db, limit=limit)


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.get("/{book_id}/bsr-history", response_model=BookBSRHistoryRead)
def get_book_bsr_history_route(
    book_id: int,
    limit: int = Query(default=90, ge=1, le=365),
    db: Session = Depends(get_db),
) -> BookBSRHistoryRead:
    try:
        return get_book_bsr_history(db, book_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{book_id}/collect-details", response_model=BookDetailCollectionRead)
def collect_book_details(book_id: int, db: Session = Depends(get_db)) -> BookDetailCollectionRead:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return collect_and_store_book_details(db, book)


@router.get("/{book_id}/insight", response_model=BookInsightRead)
def get_book_insight(book_id: int, db: Session = Depends(get_db)) -> BookInsightRead:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    insight = db.scalars(select(BookInsight).where(BookInsight.book_id == book_id)).first()
    if insight is None:
        raise HTTPException(status_code=404, detail="Book insight not found")
    return BookInsightRead.model_validate(insight)


@router.post("/{book_id}/refresh-insight", response_model=BookInsightRead)
def refresh_book_insight(book_id: int, db: Session = Depends(get_db)) -> BookInsightRead:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    insight = upsert_book_insight(db, book)
    if insight is None:
        raise HTTPException(status_code=400, detail="Book has no extractable listing text")
    return BookInsightRead.model_validate(insight)


@router.post("/{book_id}/collect-reviews", response_model=list[ReviewRead])
def collect_book_reviews(
    book_id: int,
    page: int = Query(default=1, ge=1, le=10),
    db: Session = Depends(get_db),
) -> list[ReviewRead]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return collect_and_store_reviews(db, book, page=page)


@router.get("/{book_id}/reviews", response_model=list[ReviewRead])
def list_book_reviews(book_id: int, db: Session = Depends(get_db)) -> list[ReviewRead]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return [
        ReviewRead.model_validate(review)
        for review in db.scalars(
            select(Review)
            .where(Review.book_id == book_id)
            .order_by(Review.review_date.desc().nullslast(), Review.id.desc())
        )
    ]


@router.post("/{book_id}/analyze-reviews", response_model=list[ReviewClusterRead])
def analyze_reviews_for_book(book_id: int, db: Session = Depends(get_db)) -> list[ReviewClusterRead]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return analyze_book_reviews(db, book)


@router.get("/{book_id}/review-clusters", response_model=list[ReviewClusterRead])
def list_book_review_clusters(book_id: int, db: Session = Depends(get_db)) -> list[ReviewClusterRead]:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return list_review_clusters_for_book(db, book_id)
