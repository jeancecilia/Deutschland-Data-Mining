from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book


class BookInsight(Base, TimestampMixin):
    __tablename__ = "book_insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="heuristic")
    model_name: Mapped[str | None] = mapped_column(String(100))
    semantic_key: Mapped[str | None] = mapped_column(String(255), index=True)
    semantic_summary: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(String(255))
    core_problem: Mapped[str | None] = mapped_column(String(255))
    use_case: Mapped[str | None] = mapped_column(String(255))
    promised_outcome: Mapped[str | None] = mapped_column(String(255))
    book_format: Mapped[str | None] = mapped_column(String(100))
    feature_terms: Mapped[list[str] | None] = mapped_column(JSON)
    category_terms: Mapped[list[str] | None] = mapped_column(JSON)
    quality_flags: Mapped[list[str] | None] = mapped_column(JSON)
    localization_notes: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[int | None] = mapped_column(Integer)
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSON)

    book: Mapped["Book"] = relationship(back_populates="ai_insight")
