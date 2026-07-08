from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.keyword import Keyword
    from app.models.report import Report, SachbuchOpportunityScore, SachbuchTopicGap


class NicheCluster(Base, TimestampMixin):
    __tablename__ = "niche_clusters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    marketplace: Mapped[str] = mapped_column(String(16), nullable=False, default="amazon.de")
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="de")
    main_keyword: Mapped[str | None] = mapped_column(String(255))
    book_class: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")

    keyword_links: Mapped[list["NicheClusterKeyword"]] = relationship(
        back_populates="niche_cluster", cascade="all, delete-orphan"
    )
    book_links: Mapped[list["NicheClusterBook"]] = relationship(
        back_populates="niche_cluster", cascade="all, delete-orphan"
    )
    opportunity_scores: Mapped[list["OpportunityScore"]] = relationship(
        back_populates="niche_cluster", cascade="all, delete-orphan"
    )
    sachbuch_topic_gaps: Mapped[list["SachbuchTopicGap"]] = relationship(
        back_populates="niche_cluster", cascade="all, delete-orphan"
    )
    sachbuch_opportunity_scores: Mapped[list["SachbuchOpportunityScore"]] = relationship(
        back_populates="niche_cluster", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="niche_cluster", cascade="all, delete-orphan"
    )


class NicheClusterKeyword(Base):
    __tablename__ = "niche_cluster_keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    niche_cluster_id: Mapped[int] = mapped_column(
        ForeignKey("niche_clusters.id"), nullable=False, index=True
    )
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    relevance_score: Mapped[int | None] = mapped_column(Integer)

    niche_cluster: Mapped["NicheCluster"] = relationship(back_populates="keyword_links")
    keyword: Mapped["Keyword"] = relationship(back_populates="niche_cluster_links")


class NicheClusterBook(Base):
    __tablename__ = "niche_cluster_books"

    id: Mapped[int] = mapped_column(primary_key=True)
    niche_cluster_id: Mapped[int] = mapped_column(
        ForeignKey("niche_clusters.id"), nullable=False, index=True
    )
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    relevance_score: Mapped[int | None] = mapped_column(Integer)

    niche_cluster: Mapped["NicheCluster"] = relationship(back_populates="book_links")
    book: Mapped["Book"] = relationship(back_populates="niche_cluster_links")


class OpportunityScore(Base, TimestampMixin):
    __tablename__ = "opportunity_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    niche_cluster_id: Mapped[int] = mapped_column(
        ForeignKey("niche_clusters.id"), nullable=False, index=True
    )
    keyword_specificity_score: Mapped[int | None] = mapped_column(Integer)
    new_entrant_signal: Mapped[int | None] = mapped_column(Integer)
    review_insight_score: Mapped[int | None] = mapped_column(Integer)
    demand_score: Mapped[int | None] = mapped_column(Integer)
    saturation_risk: Mapped[int | None] = mapped_column(Integer)
    entry_feasibility_score: Mapped[int | None] = mapped_column(Integer)
    review_wall_risk: Mapped[int | None] = mapped_column(Integer)
    differentiation_score: Mapped[int | None] = mapped_column(Integer)
    ai_slop_score: Mapped[int | None] = mapped_column(Integer)
    brand_dominance_risk: Mapped[int | None] = mapped_column(Integer)
    content_complexity_risk: Mapped[int | None] = mapped_column(Integer)
    compliance_risk: Mapped[int | None] = mapped_column(Integer)
    price_compression_risk: Mapped[int | None] = mapped_column(Integer)
    authority_risk: Mapped[int | None] = mapped_column(Integer)
    research_effort_score: Mapped[int | None] = mapped_column(Integer)
    final_score: Mapped[int | None] = mapped_column(Integer)
    explanation: Mapped[str | None] = mapped_column(Text)

    niche_cluster: Mapped["NicheCluster"] = relationship(back_populates="opportunity_scores")
