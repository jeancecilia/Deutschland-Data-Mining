from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    rating: int | None
    title: str | None
    body: str | None
    review_date: date | None
    verified_purchase: bool | None
    helpful_count: int | None
    language: str
    captured_at: datetime

