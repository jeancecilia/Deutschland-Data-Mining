from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class BSRSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    marketplace: str
    bsr_main: int | None
    category_bsr_1: int | None
    category_bsr_2: int | None
    category_bsr_3: int | None
    captured_at: datetime
    source: str


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asin: str
    title: str | None
    subtitle: str | None
    author: str | None
    publisher: str | None
    marketplace: str
    formats: str | None
    publication_date: date | None
    page_count: int | None
    description: str | None
    cover_url: str | None
    edition_info: str | None
    primary_category: str | None
    secondary_category: str | None
    tertiary_category: str | None
    table_of_contents: str | None
    book_class: str | None
    created_at: datetime
    updated_at: datetime


class BookDetailCollectionRead(BaseModel):
    book: BookRead
    latest_bsr_snapshot: BSRSnapshotRead | None


class BSRHistorySummaryRead(BaseModel):
    snapshot_count: int
    latest_bsr: int | None
    average_bsr: float | None
    median_bsr: float | None
    volatility: float | None
    trend: str
    stability: int | None
    improvement: int | None
    decay: int | None


class BookBSRHistoryRead(BaseModel):
    book: BookRead
    summary: BSRHistorySummaryRead
    history: list[BSRSnapshotRead]


class BSRRefreshItemRead(BaseModel):
    book_id: int
    asin: str
    title: str | None
    status: str
    skipped_reason: str | None
    latest_bsr_snapshot: BSRSnapshotRead | None


class ClusterBSRRefreshRead(BaseModel):
    cluster_id: int
    cluster_name: str
    requested_limit: int
    min_hours_between_snapshots: int
    processed_count: int
    refreshed_count: int
    skipped_count: int
    failed_count: int
    items: list[BSRRefreshItemRead]
