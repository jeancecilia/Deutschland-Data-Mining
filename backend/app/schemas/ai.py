from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BookInsightRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    provider: str
    model_name: str | None
    semantic_key: str | None
    semantic_summary: str | None
    target_audience: str | None
    core_problem: str | None
    use_case: str | None
    promised_outcome: str | None
    book_format: str | None
    feature_terms: list[str] | None
    category_terms: list[str] | None
    quality_flags: list[str] | None
    localization_notes: str | None
    confidence: int | None
    created_at: datetime
    updated_at: datetime
