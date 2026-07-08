from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.review import Review
from app.schemas.review import ReviewRead
from app.services.amazon_reviews import fetch_reviews


def collect_and_store_reviews(db: Session, book: Book, *, page: int = 1) -> list[ReviewRead]:
    review_items = fetch_reviews(book.asin, page=page)
    persisted: list[Review] = []

    for item in review_items:
        existing = db.scalars(
            select(Review).where(
                Review.book_id == book.id,
                Review.title == item.title,
                Review.body == item.body,
                Review.review_date == item.review_date,
            )
        ).first()
        if existing is not None:
            persisted.append(existing)
            continue

        review = Review(
            book_id=book.id,
            rating=item.rating,
            title=item.title,
            body=item.body,
            review_date=item.review_date,
            verified_purchase=item.verified_purchase,
            helpful_count=item.helpful_count,
            language=item.language,
            captured_at=item.captured_at,
        )
        db.add(review)
        persisted.append(review)

    db.commit()

    fresh_reviews = list(
        db.scalars(
            select(Review)
            .where(Review.book_id == book.id)
            .order_by(Review.review_date.desc().nullslast(), Review.id.desc())
        )
    )
    return [ReviewRead.model_validate(review) for review in fresh_reviews]

