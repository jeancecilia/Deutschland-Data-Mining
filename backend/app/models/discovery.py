from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DiscoveryTopic(Base, TimestampMixin):
    __tablename__ = "discovery_topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category_hint: Mapped[str | None] = mapped_column(String(255))
    book_type_hint: Mapped[str | None] = mapped_column(String(50))
    risk_level: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class DiscoveryAudience(Base, TimestampMixin):
    __tablename__ = "discovery_audiences"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class DiscoveryPainPoint(Base, TimestampMixin):
    __tablename__ = "discovery_pain_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class DiscoveryContext(Base, TimestampMixin):
    __tablename__ = "discovery_contexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class DiscoveryBookFormat(Base, TimestampMixin):
    __tablename__ = "discovery_book_formats"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    book_type_hint: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class DiscoveryRun(Base, TimestampMixin):
    __tablename__ = "discovery_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="cycle")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    requested_generate_limit: Mapped[int | None] = mapped_column(Integer)
    requested_validate_limit: Mapped[int | None] = mapped_column(Integer)
    generated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kept_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_generate_reports: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text)


class DiscoveryCandidate(Base, TimestampMixin):
    __tablename__ = "discovery_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    discovery_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("discovery_runs.id"), index=True
    )
    topic_id: Mapped[int] = mapped_column(ForeignKey("discovery_topics.id"), nullable=False, index=True)
    audience_id: Mapped[int | None] = mapped_column(ForeignKey("discovery_audiences.id"), index=True)
    pain_point_id: Mapped[int | None] = mapped_column(
        ForeignKey("discovery_pain_points.id"), index=True
    )
    context_id: Mapped[int | None] = mapped_column(ForeignKey("discovery_contexts.id"), index=True)
    book_format_id: Mapped[int | None] = mapped_column(
        ForeignKey("discovery_book_formats.id"), index=True
    )
    candidate_phrase: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_phrase: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    semantic_key: Mapped[str | None] = mapped_column(String(255), index=True)
    semantic_family: Mapped[str | None] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="de")
    marketplace: Mapped[str] = mapped_column(String(16), nullable=False, default="amazon.de")
    book_type_hint: Mapped[str | None] = mapped_column(String(50))
    validated_book_type: Mapped[str | None] = mapped_column(String(50))
    risk_level: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="generated")
    generation_score: Mapped[int | None] = mapped_column(Integer)
    specificity_score: Mapped[int | None] = mapped_column(Integer)
    intent_score: Mapped[int | None] = mapped_column(Integer)
    audience_clarity_score: Mapped[int | None] = mapped_column(Integer)
    format_suitability_score: Mapped[int | None] = mapped_column(Integer)
    competition_probability_score: Mapped[int | None] = mapped_column(Integer)
    production_effort_score: Mapped[int | None] = mapped_column(Integer)
    pain_clarity_score: Mapped[int | None] = mapped_column(Integer)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), index=True)
    niche_cluster_id: Mapped[int | None] = mapped_column(
        ForeignKey("niche_clusters.id"), index=True
    )
    validated_target_audience: Mapped[str | None] = mapped_column(String(255))
    demand_score: Mapped[int | None] = mapped_column(Integer)
    competition_score: Mapped[int | None] = mapped_column(Integer)
    gap_score: Mapped[int | None] = mapped_column(Integer)
    production_difficulty_score: Mapped[int | None] = mapped_column(Integer)
    risk_score: Mapped[int | None] = mapped_column(Integer)
    final_opportunity_score: Mapped[int | None] = mapped_column(Integer)
    decision: Mapped[str | None] = mapped_column(String(50))
    relevant_book_count: Mapped[int | None] = mapped_column(Integer)
    related_keyword_count: Mapped[int | None] = mapped_column(Integer)
    top_competitor_review_median: Mapped[int | None] = mapped_column(Integer)
    bsr_coverage: Mapped[int | None] = mapped_column(Integer)
    report_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    market_summary: Mapped[str | None] = mapped_column(Text)
    gap_summary: Mapped[str | None] = mapped_column(Text)
    reason_summary: Mapped[str | None] = mapped_column(Text)
    recommended_angle: Mapped[str | None] = mapped_column(Text)
    validation_notes: Mapped[str | None] = mapped_column(Text)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
