from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.ai import BookInsight
    from app.models.niche import NicheClusterBook
    from app.models.review import Review, ReviewCluster
    from app.models.run import BSRSnapshot, SearchResult


class Book(Base, TimestampMixin):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    asin: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    subtitle: Mapped[str | None] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(255))
    publisher: Mapped[str | None] = mapped_column(String(255))
    marketplace: Mapped[str] = mapped_column(String(16), nullable=False, default="amazon.de")
    formats: Mapped[str | None] = mapped_column(String(255))
    publication_date: Mapped[date | None] = mapped_column(Date)
    page_count: Mapped[int | None]
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(1000))
    edition_info: Mapped[str | None] = mapped_column(String(255))
    primary_category: Mapped[str | None] = mapped_column(String(255))
    secondary_category: Mapped[str | None] = mapped_column(String(255))
    tertiary_category: Mapped[str | None] = mapped_column(String(255))
    table_of_contents: Mapped[str | None] = mapped_column(Text)
    book_class: Mapped[str | None] = mapped_column(String(50))

    search_results: Mapped[list["SearchResult"]] = relationship(back_populates="book")
    bsr_snapshots: Mapped[list["BSRSnapshot"]] = relationship(back_populates="book")
    reviews: Mapped[list["Review"]] = relationship(back_populates="book")
    review_clusters: Mapped[list["ReviewCluster"]] = relationship(back_populates="book")
    ai_insight: Mapped["BookInsight | None"] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        uselist=False,
    )
    niche_cluster_links: Mapped[list["NicheClusterBook"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
