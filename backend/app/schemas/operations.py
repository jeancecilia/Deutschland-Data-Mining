from datetime import datetime

from pydantic import BaseModel


class RecentCrawlRead(BaseModel):
    run_id: int
    keyword_id: int
    keyword: str
    run_at: datetime
    status: str
    result_count: int | None
    notes: str | None


class FailedJobRead(BaseModel):
    job_type: str
    reference: str
    occurred_at: datetime
    status: str
    notes: str | None


class OperationsSummaryRead(BaseModel):
    last_crawl_at: datetime | None
    last_bsr_snapshot_at: datetime | None
    failed_job_count: int
    recent_crawls: list[RecentCrawlRead]
    failed_jobs: list[FailedJobRead]
