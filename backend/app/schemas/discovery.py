from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.signal import OpportunitySignalRead


class DiscoveryUniverseItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    priority: int
    active: bool
    category_hint: str | None = None
    book_type_hint: str | None = None
    risk_level: str | None = None


class DiscoveryUniverseRead(BaseModel):
    topics: list[DiscoveryUniverseItemRead]
    audiences: list[DiscoveryUniverseItemRead]
    pain_points: list[DiscoveryUniverseItemRead]
    contexts: list[DiscoveryUniverseItemRead]
    book_formats: list[DiscoveryUniverseItemRead]


class DiscoveryCandidateRead(BaseModel):
    id: int
    topic: str
    audience: str | None
    pain_point: str | None
    context: str | None
    book_format: str | None
    candidate_phrase: str
    semantic_key: str | None
    semantic_family: str | None
    language: str
    marketplace: str
    book_type_hint: str | None
    validated_book_type: str | None
    risk_level: str | None
    status: str
    generation_score: int | None
    specificity_score: int | None
    intent_score: int | None
    audience_clarity_score: int | None
    format_suitability_score: int | None
    competition_probability_score: int | None
    production_effort_score: int | None
    pain_clarity_score: int | None
    validated_target_audience: str | None
    demand_score: int | None
    competition_score: int | None
    gap_score: int | None
    production_difficulty_score: int | None
    risk_score: int | None
    final_opportunity_score: int | None
    decision: str | None
    keyword_id: int | None
    niche_cluster_id: int | None
    relevant_book_count: int | None
    related_keyword_count: int | None
    top_competitor_review_median: int | None
    bsr_coverage: int | None
    report_count: int
    market_summary: str | None
    gap_summary: str | None
    reason_summary: str | None
    recommended_angle: str | None
    validation_notes: str | None
    signals: list[OpportunitySignalRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    last_validated_at: datetime | None


class DiscoveryGenerateRead(BaseModel):
    run_id: int
    generated_count: int
    updated_count: int
    deduplicated_count: int
    candidates: list[DiscoveryCandidateRead]


class DiscoveryCycleRead(BaseModel):
    run_id: int
    generated_count: int
    updated_count: int
    deduplicated_count: int
    validated_count: int
    kept_count: int
    failed_count: int
    report_count: int
    candidates: list[DiscoveryCandidateRead]
