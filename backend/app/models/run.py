from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.keyword import Keyword


class SearchRun(Base):
    __tablename__ = "search_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    marketplace: Mapped[str] = mapped_column(String(16), nullable=False, default="amazon.de")
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="organic_search")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    result_count: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)

    keyword: Mapped["Keyword"] = relationship(back_populates="search_runs")
    search_results: Mapped[list["SearchResult"]] = relationship(
        back_populates="search_run", cascade="all, delete-orphan"
    )


class SearchResult(Base):
    __tablename__ = "search_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    search_run_id: Mapped[int] = mapped_column(ForeignKey("search_runs.id"), nullable=False, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(nullable=False)
    is_sponsored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    rating: Mapped[float | None]
    review_count: Mapped[int | None]
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    search_run: Mapped["SearchRun"] = relationship(back_populates="search_results")
    book: Mapped["Book"] = relationship(back_populates="search_results")


class BSRSnapshot(Base):
    __tablename__ = "bsr_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    marketplace: Mapped[str] = mapped_column(String(16), nullable=False, default="amazon.de")
    bsr_main: Mapped[int | None]
    category_bsr_1: Mapped[int | None]
    category_bsr_2: Mapped[int | None]
    category_bsr_3: Mapped[int | None]
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="listing")

    book: Mapped["Book"] = relationship(back_populates="bsr_snapshots")

