from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    rating: Mapped[int | None]
    title: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str | None] = mapped_column(Text)
    review_date: Mapped[date | None] = mapped_column(Date)
    verified_purchase: Mapped[bool | None] = mapped_column(Boolean)
    helpful_count: Mapped[int | None]
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="de")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    book: Mapped["Book"] = relationship(back_populates="reviews")


class ReviewCluster(Base, TimestampMixin):
    __tablename__ = "review_clusters"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    cluster_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[int | None]
    severity: Mapped[int | None]
    summary: Mapped[str | None] = mapped_column(Text)
    example_snippets: Mapped[str | None] = mapped_column(Text)
    suggested_improvements: Mapped[str | None] = mapped_column(Text)
    cluster_type: Mapped[str | None] = mapped_column(String(50))
    theme_key: Mapped[str | None] = mapped_column(String(100))
    semantic_key: Mapped[str | None] = mapped_column(String(255), index=True)
    source_method: Mapped[str | None] = mapped_column(String(50))
    confidence_score: Mapped[int | None] = mapped_column(Integer)
    buyer_words: Mapped[list[str] | None] = mapped_column(JSON)
    audience_hint: Mapped[str | None] = mapped_column(String(255))
    missing_feature: Mapped[str | None] = mapped_column(String(255))
    evidence_terms: Mapped[list[str] | None] = mapped_column(JSON)

    book: Mapped["Book"] = relationship(back_populates="review_clusters")
