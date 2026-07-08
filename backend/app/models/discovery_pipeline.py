"""
Discovery Pipeline Models — Initial Discovery Layer (Teil A).

Tables:
  discovery_sources        — Registered data sources
  raw_discovery_items      — Raw collected text from sources
  discovery_entities       — Extracted structured concepts
  discovery_entity_aliases — Alternative names for entities
  discovery_entity_relations — Topic Graph edges
  niche_candidates         — Composed KDP niche ideas
  niche_candidate_keywords — Keyword variants per candidate
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


# ── discovery_sources ──────────────────────────────────────────────────────


class DiscoverySource(Base, TimestampMixin):
    """A registered external data source for raw topic discovery."""

    __tablename__ = "discovery_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="public_list, marketplace_category, autocomplete_source, "
                "forum_question_source, wikipedia_category, profession_list, "
                "exam_list, life_event_list, hobby_list, etc.",
    )
    source_url: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="de")
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="DE")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rate_limit_config: Mapped[dict | None] = mapped_column(JSONB)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)


# ── raw_discovery_items ────────────────────────────────────────────────────


class RawDiscoveryItem(Base, TimestampMixin):
    """A single raw text snippet collected from a discovery source."""

    __tablename__ = "raw_discovery_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    discovery_source_id: Mapped[int | None] = mapped_column(
        ForeignKey("discovery_sources.id"), index=True,
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    raw_url: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="de")
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="DE")
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="new",
        comment="new, processed, ignored, failed, needs_review",
    )
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── discovery_entities ─────────────────────────────────────────────────────


class DiscoveryEntity(Base, TimestampMixin):
    """A structured concept extracted from raw_items or declared manually.

    Entity types: topic, audience, profession, problem, life_event, object,
    hobby, skill, exam, book_format, outcome, risk_area, location_context,
    age_group, family_role, business_type.
    """

    __tablename__ = "discovery_entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="de")
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="DE")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("normalized_name", "entity_type", "language", name="uq_de_normalized"),
    )


# ── discovery_entity_aliases ───────────────────────────────────────────────


class DiscoveryEntityAlias(Base, TimestampMixin):
    """Alternative surface forms for a DiscoveryEntity."""

    __tablename__ = "discovery_entity_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("discovery_entities.id"), nullable=False, index=True,
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="de")

    __table_args__ = (
        UniqueConstraint("entity_id", "alias", name="uq_de_alias"),
    )


# ── discovery_entity_relations ─────────────────────────────────────────────


class DiscoveryEntityRelation(Base, TimestampMixin):
    """A directed, typed edge in the Topic Graph."""

    __tablename__ = "discovery_entity_relations"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_entity_id: Mapped[int] = mapped_column(
        ForeignKey("discovery_entities.id"), nullable=False, index=True,
    )
    target_entity_id: Mapped[int] = mapped_column(
        ForeignKey("discovery_entities.id"), nullable=False, index=True,
    )
    relation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="subtopic_of, has_problem, problem_for, used_by, "
                "belongs_to_audience, belongs_to_profession, has_exam, "
                "has_life_event, has_use_case, suitable_format, related_to, "
                "requires_authority, high_risk_topic, low_risk_topic",
    )
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    evidence_source: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint(
            "source_entity_id", "target_entity_id", "relation_type",
            name="uq_de_relation",
        ),
    )


# ── niche_candidates ───────────────────────────────────────────────────────


class NicheCandidate(Base, TimestampMixin):
    """A composed KDP niche idea, built from entities and templates."""

    __tablename__ = "niche_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True,
    )
    main_topic_entity_id: Mapped[int | None] = mapped_column(
        ForeignKey("discovery_entities.id"), index=True,
    )
    audience_entity_id: Mapped[int | None] = mapped_column(
        ForeignKey("discovery_entities.id"), index=True,
    )
    problem_entity_id: Mapped[int | None] = mapped_column(
        ForeignKey("discovery_entities.id"), index=True,
    )
    format_entity_id: Mapped[int | None] = mapped_column(
        ForeignKey("discovery_entities.id"), index=True,
    )
    book_class_guess: Mapped[str | None] = mapped_column(
        String(50), comment="sachbuch, medium_content, low_content",
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="de")
    marketplace: Mapped[str] = mapped_column(String(16), nullable=False, default="amazon.de")
    generation_template: Mapped[str | None] = mapped_column(Text)
    source_entities: Mapped[dict | None] = mapped_column(
        JSONB, comment="Snapshot of entity IDs that produced this candidate",
    )
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    risk_level: Mapped[str | None] = mapped_column(
        String(50), comment="low, medium, high",
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="new",
        comment="new, fast_validated, rejected, promoted_to_seed, "
                "sent_to_keyword_expansion, needs_manual_review",
    )
    fast_validation_score: Mapped[int | None] = mapped_column(Integer)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    promotion_reason: Mapped[str | None] = mapped_column(Text)
    # ── Quality hardening fields ──────────────────────────────────
    risk_category: Mapped[str | None] = mapped_column(String(50), comment="low, medium, high, restricted, blocked")
    risk_reason_codes: Mapped[list[str] | None] = mapped_column(JSONB)
    manual_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    authority_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disclaimer_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_promote_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    compatibility_score: Mapped[int | None] = mapped_column(Integer)
    suggested_rewrites: Mapped[list[str] | None] = mapped_column(JSONB)
    recommendation_label: Mapped[str | None] = mapped_column(String(50), comment="GO, MAYBE, NO-GO, REVIEW_REQUIRED, HIGH_RISK_OPPORTUNITY, BLOCKED")


# ── niche_candidate_keywords ───────────────────────────────────────────────


class NicheCandidateKeyword(Base, TimestampMixin):
    """Keyword variants generated for a niche candidate."""

    __tablename__ = "niche_candidate_keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    niche_candidate_id: Mapped[int] = mapped_column(
        ForeignKey("niche_candidates.id"), nullable=False, index=True,
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    keyword_type: Mapped[str | None] = mapped_column(
        String(50), comment="primary, variant, long_tail, autocomplete",
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="de")
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
