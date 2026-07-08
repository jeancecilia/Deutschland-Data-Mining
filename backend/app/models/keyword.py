from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.niche import NicheClusterKeyword
    from app.models.run import SearchRun


class Keyword(Base, TimestampMixin):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="de")
    marketplace: Mapped[str] = mapped_column(String(16), nullable=False, default="amazon.de")
    seed_keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"))
    keyword_type: Mapped[str | None] = mapped_column(String(50))
    target_audience: Mapped[str | None] = mapped_column(String(255))
    category_hint: Mapped[str | None] = mapped_column(String(255))
    search_intent_family: Mapped[str | None] = mapped_column(String(50))
    specificity_score: Mapped[int | None] = mapped_column(Integer)
    intent_score: Mapped[int | None] = mapped_column(Integer)
    audience_clarity_score: Mapped[int | None] = mapped_column(Integer)
    format_suitability_score: Mapped[int | None] = mapped_column(Integer)
    competition_probability_score: Mapped[int | None] = mapped_column(Integer)
    production_effort_score: Mapped[int | None] = mapped_column(Integer)
    book_type: Mapped[str | None] = mapped_column(String(50))
    risk_level: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    source_niche_candidate_id: Mapped[int | None] = mapped_column(ForeignKey("niche_candidates.id"), nullable=True, index=True)
    discovery_origin_type: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None, comment="initial_discovery, manual, etc.")

    seed_keyword: Mapped["Keyword | None"] = relationship(remote_side=[id])
    search_runs: Mapped[list["SearchRun"]] = relationship(back_populates="keyword")
    niche_cluster_links: Mapped[list["NicheClusterKeyword"]] = relationship(
        back_populates="keyword", cascade="all, delete-orphan"
    )
