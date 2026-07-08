"""Pydantic schemas for the Initial Discovery Pipeline."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Discovery Source ────────────────────────────────────────────────────────


class DiscoverySourceCreate(BaseModel):
    name: str
    source_type: str
    source_url: str | None = None
    language: str = "de"
    country: str = "DE"
    is_active: bool = True
    rate_limit_config: dict | None = None
    metadata_json: dict | None = None


class DiscoverySourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_type: str
    source_url: str | None
    language: str
    country: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DiscoverySourceUpdate(BaseModel):
    name: str | None = None
    source_type: str | None = None
    source_url: str | None = None
    is_active: bool | None = None
    rate_limit_config: dict | None = None
    metadata_json: dict | None = None


# ── Raw Discovery Item ──────────────────────────────────────────────────────


class RawDiscoveryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    discovery_source_id: int | None
    raw_text: str
    raw_url: str | None
    language: str
    country: str
    confidence: int
    status: str
    collected_at: datetime
    processed_at: datetime | None
    created_at: datetime


# ── Discovery Entity ────────────────────────────────────────────────────────


class DiscoveryEntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    normalized_name: str
    entity_type: str
    language: str
    confidence: float
    source_count: int
    metadata_json: dict | None
    created_at: datetime


class DiscoveryEntityCreate(BaseModel):
    name: str
    normalized_name: str
    entity_type: str
    language: str = "de"
    confidence: float = 0.5
    metadata_json: dict | None = None


# ── Discovery Entity Alias ──────────────────────────────────────────────────


class DiscoveryEntityAliasRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_id: int
    alias: str
    language: str


# ── Discovery Entity Relation ───────────────────────────────────────────────


class DiscoveryEntityRelationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_entity_id: int
    target_entity_id: int
    source_entity_name: str | None = None
    target_entity_name: str | None = None
    relation_type: str
    weight: float
    confidence: float
    evidence_source: str | None


class DiscoveryEntityRelationCreate(BaseModel):
    source_entity_id: int
    target_entity_id: int
    relation_type: str
    weight: float = 1.0
    confidence: float = 0.5
    evidence_source: str | None = None


# ── Niche Candidate ─────────────────────────────────────────────────────────


class NicheCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_name: str
    normalized_name: str
    main_topic_entity_id: int | None
    audience_entity_id: int | None
    problem_entity_id: int | None
    format_entity_id: int | None
    book_class_guess: str | None
    language: str
    marketplace: str
    generation_template: str | None
    confidence: int
    risk_level: str | None
    status: str
    fast_validation_score: int | None
    rejection_reason: str | None
    promotion_reason: str | None
    # Quality hardening fields
    risk_category: str | None = None
    risk_reason_codes: list[str] | None = None
    manual_review_required: bool = False
    authority_required: bool = False
    disclaimer_required: bool = False
    auto_promote_allowed: bool = True
    compatibility_score: int | None = None
    suggested_rewrites: list[str] | None = None
    recommendation_label: str | None = None
    created_at: datetime
    updated_at: datetime

    # Denormalised entity names for display
    main_topic: str | None = None
    audience: str | None = None
    problem: str | None = None
    format: str | None = None


class NicheCandidateUpdate(BaseModel):
    status: str | None = None
    rejection_reason: str | None = None
    promotion_reason: str | None = None
    risk_level: str | None = None
    confidence: int | None = None


class NicheCandidateKeywordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    niche_candidate_id: int
    keyword: str
    keyword_type: str | None
    language: str
    confidence: int


# ── Discovery Pipeline Overview ─────────────────────────────────────────────


class DiscoveryOverviewRead(BaseModel):
    source_count: int
    active_source_count: int
    raw_item_count: int
    unprocessed_raw_count: int
    entity_count: int
    entity_types: dict[str, int] = {}
    domain_count: int = 0
    top_domains: list[dict[str, object]] = []
    relation_count: int
    candidate_count: int
    new_candidate_count: int
    promoted_candidate_count: int
    rejected_candidate_count: int
