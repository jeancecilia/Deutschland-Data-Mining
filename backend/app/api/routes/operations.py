from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.keyword import Keyword
from app.models.report import Report
from app.models.run import BSRSnapshot, SearchRun
from app.schemas.operations import FailedJobRead, OperationsSummaryRead, RecentCrawlRead


router = APIRouter()


@router.get("/summary", response_model=OperationsSummaryRead)
def get_operations_summary(db: Session = Depends(get_db)) -> OperationsSummaryRead:
    recent_crawl_rows = db.execute(
        select(SearchRun, Keyword)
        .join(Keyword, SearchRun.keyword_id == Keyword.id)
        .order_by(SearchRun.run_at.desc(), SearchRun.id.desc())
        .limit(8)
    ).all()
    failed_search_runs = db.execute(
        select(SearchRun, Keyword)
        .join(Keyword, SearchRun.keyword_id == Keyword.id)
        .where(SearchRun.status == "failed")
        .order_by(SearchRun.run_at.desc(), SearchRun.id.desc())
        .limit(5)
    ).all()
    failed_reports = list(
        db.scalars(
            select(Report)
            .where(Report.status == "failed")
            .order_by(Report.updated_at.desc(), Report.id.desc())
            .limit(5)
        )
    )

    last_crawl = db.scalars(select(SearchRun).order_by(SearchRun.run_at.desc(), SearchRun.id.desc())).first()
    last_bsr_snapshot = db.scalars(
        select(BSRSnapshot).order_by(BSRSnapshot.captured_at.desc(), BSRSnapshot.id.desc())
    ).first()

    failed_jobs = [
        FailedJobRead(
            job_type="search_run",
            reference=keyword.keyword,
            occurred_at=run.run_at,
            status=run.status,
            notes=run.notes,
        )
        for run, keyword in failed_search_runs
    ]
    failed_jobs.extend(
        FailedJobRead(
            job_type="report",
            reference=report.title,
            occurred_at=report.updated_at,
            status=report.status,
            notes=report.report_type,
        )
        for report in failed_reports
    )
    failed_jobs.sort(key=lambda job: job.occurred_at, reverse=True)

    return OperationsSummaryRead(
        last_crawl_at=last_crawl.run_at if last_crawl else None,
        last_bsr_snapshot_at=last_bsr_snapshot.captured_at if last_bsr_snapshot else None,
        failed_job_count=len(failed_jobs),
        recent_crawls=[
            RecentCrawlRead(
                run_id=run.id,
                keyword_id=keyword.id,
                keyword=keyword.keyword,
                run_at=run.run_at,
                status=run.status,
                result_count=run.result_count,
                notes=run.notes,
            )
            for run, keyword in recent_crawl_rows
        ],
        failed_jobs=failed_jobs[:5],
    )
