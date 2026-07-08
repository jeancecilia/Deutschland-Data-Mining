from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReviewClusterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    cluster_name: str
    sentiment: str
    frequency: int | None
    severity: int | None
    summary: str | None
    example_snippets: str | None
    suggested_improvements: str | None
    cluster_type: str | None
    theme_key: str | None
    semantic_key: str | None
    source_method: str | None
    confidence_score: int | None
    buyer_words: list[str] | None
    audience_hint: str | None
    missing_feature: str | None
    evidence_terms: list[str] | None
    created_at: datetime
    updated_at: datetime
