from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KeywordCreate(BaseModel):
    keyword: str = Field(min_length=2, max_length=255)
    language: str = "de"
    marketplace: str = "amazon.de"
    status: str = "new"
    keyword_type: str | None = None
    target_audience: str | None = None
    category_hint: str | None = None
    book_type: str | None = None
    risk_level: str | None = None
    priority: int = Field(default=0, ge=0, le=100)
    notes: str | None = None


class KeywordUpdate(BaseModel):
    status: str | None = Field(default=None, min_length=2, max_length=50)
    keyword_type: str | None = None
    book_type: str | None = None
    risk_level: str | None = None
    target_audience: str | None = None
    category_hint: str | None = None
    search_intent_family: str | None = None
    priority: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class KeywordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str
    language: str
    marketplace: str
    seed_keyword_id: int | None
    status: str
    keyword_type: str | None
    target_audience: str | None
    category_hint: str | None
    search_intent_family: str | None
    specificity_score: int | None
    intent_score: int | None
    audience_clarity_score: int | None
    format_suitability_score: int | None
    competition_probability_score: int | None
    production_effort_score: int | None
    book_type: str | None
    risk_level: str | None
    priority: int
    notes: str | None
    created_at: datetime
    updated_at: datetime


class KeywordExpansionRead(BaseModel):
    keyword: str
    keyword_type: str


class KeywordExpansionResponse(BaseModel):
    seed_keyword_id: int
    seed_keyword: str
    expansions: list[KeywordExpansionRead]
