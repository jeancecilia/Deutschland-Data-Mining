from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.niche import NicheCluster


class SachbuchTopicGap(Base, TimestampMixin):
    __tablename__ = "sachbuch_topic_gaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    niche_cluster_id: Mapped[int] = mapped_column(
        ForeignKey("niche_clusters.id"), nullable=False, index=True
    )
    topic_gap_summary: Mapped[str | None] = mapped_column(Text)
    outdated_content_signal: Mapped[int | None] = mapped_column(Integer)
    missing_examples_signal: Mapped[int | None] = mapped_column(Integer)
    missing_checklists_signal: Mapped[int | None] = mapped_column(Integer)
    localization_gap_signal: Mapped[int | None] = mapped_column(Integer)
    content_depth_score: Mapped[int | None] = mapped_column(Integer)
    authority_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expert_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    niche_cluster: Mapped["NicheCluster"] = relationship(back_populates="sachbuch_topic_gaps")


class SachbuchOpportunityScore(Base, TimestampMixin):
    __tablename__ = "sachbuch_opportunity_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    niche_cluster_id: Mapped[int] = mapped_column(
        ForeignKey("niche_clusters.id"), nullable=False, index=True
    )
    german_demand_signal: Mapped[int | None] = mapped_column(Integer)
    topic_gap_signal: Mapped[int | None] = mapped_column(Integer)
    depth_weakness_signal: Mapped[int | None] = mapped_column(Integer)
    freshness_need_signal: Mapped[int | None] = mapped_column(Integer)
    localization_signal: Mapped[int | None] = mapped_column(Integer)
    differentiation_signal: Mapped[int | None] = mapped_column(Integer)
    evergreen_potential_signal: Mapped[int | None] = mapped_column(Integer)
    monetization_potential_signal: Mapped[int | None] = mapped_column(Integer)
    authority_risk: Mapped[int | None] = mapped_column(Integer)
    research_effort_risk: Mapped[int | None] = mapped_column(Integer)
    liability_risk: Mapped[int | None] = mapped_column(Integer)
    update_risk: Mapped[int | None] = mapped_column(Integer)
    publisher_dominance_risk: Mapped[int | None] = mapped_column(Integer)
    review_wall_risk: Mapped[int | None] = mapped_column(Integer)
    final_score: Mapped[int | None] = mapped_column(Integer)
    explanation: Mapped[str | None] = mapped_column(Text)

    niche_cluster: Mapped["NicheCluster"] = relationship(back_populates="sachbuch_opportunity_scores")


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    niche_cluster_id: Mapped[int] = mapped_column(
        ForeignKey("niche_clusters.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    markdown_content: Mapped[str | None] = mapped_column(Text)
    markdown_path: Mapped[str | None] = mapped_column(String(1000))
    pdf_path: Mapped[str | None] = mapped_column(String(1000))
    csv_path: Mapped[str | None] = mapped_column(String(1000))
    json_path: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")

    niche_cluster: Mapped["NicheCluster"] = relationship(back_populates="reports")
