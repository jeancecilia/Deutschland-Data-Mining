from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.run import BSRSnapshot
from app.schemas.book import BSRSnapshotRead, BookDetailCollectionRead, BookRead
from app.services.ai_intelligence import upsert_book_insight
from app.services.amazon_book import fetch_book_details


def collect_and_store_book_details(db: Session, book: Book) -> BookDetailCollectionRead:
    details = fetch_book_details(book.asin)

    if details.title:
        book.title = details.title
    if details.subtitle:
        book.subtitle = details.subtitle
    if details.author:
        book.author = details.author
    if details.publisher:
        book.publisher = details.publisher
    if details.formats:
        book.formats = details.formats
    if details.publication_date:
        book.publication_date = details.publication_date
    if details.page_count is not None:
        book.page_count = details.page_count
    if details.description:
        book.description = details.description
    if details.cover_url:
        book.cover_url = details.cover_url
    if details.edition_info:
        book.edition_info = details.edition_info
    if details.primary_category:
        book.primary_category = details.primary_category
    if details.secondary_category:
        book.secondary_category = details.secondary_category
    if details.tertiary_category:
        book.tertiary_category = details.tertiary_category
    if details.table_of_contents:
        book.table_of_contents = details.table_of_contents

    snapshot = BSRSnapshot(
        book_id=book.id,
        marketplace=book.marketplace,
        bsr_main=details.bsr_main,
        category_bsr_1=details.category_bsr_1,
        category_bsr_2=details.category_bsr_2,
        category_bsr_3=details.category_bsr_3,
        captured_at=datetime.now(UTC),
        source="detail_page",
    )
    db.add(snapshot)
    db.add(book)
    db.commit()
    db.refresh(book)
    db.refresh(snapshot)
    upsert_book_insight(db, book)

    return BookDetailCollectionRead(
        book=BookRead.model_validate(book),
        latest_bsr_snapshot=BSRSnapshotRead.model_validate(snapshot),
    )


def list_books(db: Session, *, limit: int = 100) -> list[Book]:
    statement = select(Book).order_by(Book.updated_at.desc()).limit(limit)
    return list(db.scalars(statement))
