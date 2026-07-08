from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SearchResultItemRead(BaseModel):
    asin: str
    title: str | None
    marketplace: str
    position: int
    is_sponsored: bool
    price: Decimal | None
    rating: float | None
    review_count: int | None
    captured_at: datetime


class SearchRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword_id: int
    marketplace: str
    run_at: datetime
    source_type: str
    status: str
    result_count: int | None
    notes: str | None


class SearchRunDetailRead(SearchRunRead):
    results: list[SearchResultItemRead]
