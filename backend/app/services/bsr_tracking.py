from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import mean, median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.niche import NicheCluster, NicheClusterBook
from app.models.run import BSRSnapshot
from app.schemas.book import (
    BSRHistorySummaryRead,
    BSRRefreshItemRead,
    BookBSRHistoryRead,
    ClusterBSRRefreshRead,
    BSRSnapshotRead,
    BookRead,
)
from app.services.book_collection import collect_and_store_book_details


def get_book_bsr_history(db: Session, book_id: int, *, limit: int = 90) -> BookBSRHistoryRead:
    book = db.get(Book, book_id)
    if book is None:
        raise ValueError("Book not found.")

    snapshots = list(
        db.scalars(
            select(BSRSnapshot)
            .where(BSRSnapshot.book_id == book.id)
            .order_by(BSRSnapshot.captured_at.desc(), BSRSnapshot.id.desc())
            .limit(limit)
        )
    )
    chronological_snapshots = list(reversed(snapshots))

    return BookBSRHistoryRead(
        book=BookRead.model_validate(book),
        summary=compute_bsr_history_summary(chronological_snapshots),
        history=[BSRSnapshotRead.model_validate(snapshot) for snapshot in chronological_snapshots],
    )


def collect_cluster_bsr_snapshots(
    db: Session,
    cluster_id: int,
    *,
    limit: int = 5,
    min_hours_between_snapshots: int = 12,
) -> ClusterBSRRefreshRead:
    cluster = db.get(NicheCluster, cluster_id)
    if cluster is None:
        raise ValueError("Cluster not found.")

    book_rows = db.execute(
        select(NicheClusterBook, Book)
        .join(Book, NicheClusterBook.book_id == Book.id)
        .where(NicheClusterBook.niche_cluster_id == cluster.id)
        .order_by(NicheClusterBook.relevance_score.desc().nullslast(), Book.id.asc())
        .limit(limit)
    ).all()

    items: list[BSRRefreshItemRead] = []
    refreshed_count = 0
    skipped_count = 0
    failed_count = 0

    for _, book in book_rows:
        status, snapshot, skipped_reason = _refresh_book_snapshot_if_due(
            db,
            book,
            min_hours_between_snapshots=min_hours_between_snapshots,
        )
        if status == "refreshed":
            refreshed_count += 1
        elif status == "skipped":
            skipped_count += 1
        else:
            failed_count += 1

        items.append(
            BSRRefreshItemRead(
                book_id=book.id,
                asin=book.asin,
                title=book.title,
                status=status,
                skipped_reason=skipped_reason,
                latest_bsr_snapshot=BSRSnapshotRead.model_validate(snapshot) if snapshot else None,
            )
        )

    return ClusterBSRRefreshRead(
        cluster_id=cluster.id,
        cluster_name=cluster.name,
        requested_limit=limit,
        min_hours_between_snapshots=min_hours_between_snapshots,
        processed_count=len(items),
        refreshed_count=refreshed_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        items=items,
    )


def refresh_recent_cluster_bsr_snapshots(
    db: Session,
    *,
    cluster_limit: int = 3,
    books_per_cluster: int = 5,
    min_hours_between_snapshots: int = 12,
) -> dict[str, int]:
    clusters = list(
        db.scalars(
            select(NicheCluster)
            .order_by(NicheCluster.updated_at.desc(), NicheCluster.id.desc())
            .limit(cluster_limit)
        )
    )

    processed_clusters = 0
    refreshed_books = 0
    skipped_books = 0
    failed_books = 0
    for cluster in clusters:
        result = collect_cluster_bsr_snapshots(
            db,
            cluster.id,
            limit=books_per_cluster,
            min_hours_between_snapshots=min_hours_between_snapshots,
        )
        processed_clusters += 1
        refreshed_books += result.refreshed_count
        skipped_books += result.skipped_count
        failed_books += result.failed_count

    return {
        "processed_clusters": processed_clusters,
        "refreshed_books": refreshed_books,
        "skipped_books": skipped_books,
        "failed_books": failed_books,
    }


def compute_bsr_history_summary(snapshots: list[BSRSnapshot]) -> BSRHistorySummaryRead:
    values = [snapshot.bsr_main for snapshot in snapshots if snapshot.bsr_main is not None]
    if not values:
        return BSRHistorySummaryRead(
            snapshot_count=len(snapshots),
            latest_bsr=None,
            average_bsr=None,
            median_bsr=None,
            volatility=None,
            trend="unknown",
            stability=None,
            improvement=None,
            decay=None,
        )

    first_value = values[0]
    latest_value = values[-1]
    max_value = max(values)
    min_value = min(values)
    volatility = round(((max_value - min_value) / max_value) * 100, 2) if max_value else 0.0
    delta = latest_value - first_value
    threshold = max(100, round(first_value * 0.05))

    if delta <= -threshold:
        trend = "improving"
    elif delta >= threshold:
        trend = "decaying"
    else:
        trend = "stable"

    return BSRHistorySummaryRead(
        snapshot_count=len(snapshots),
        latest_bsr=latest_value,
        average_bsr=round(mean(values), 2),
        median_bsr=round(median(values), 2),
        volatility=volatility,
        trend=trend,
        stability=max(0, 100 - round(volatility)),
        improvement=max(0, first_value - latest_value),
        decay=max(0, latest_value - first_value),
    )


def _refresh_book_snapshot_if_due(
    db: Session,
    book: Book,
    *,
    min_hours_between_snapshots: int,
) -> tuple[str, BSRSnapshot | None, str | None]:
    latest_snapshot = db.scalars(
        select(BSRSnapshot)
        .where(BSRSnapshot.book_id == book.id)
        .order_by(BSRSnapshot.captured_at.desc(), BSRSnapshot.id.desc())
    ).first()

    now = datetime.now(UTC)
    if latest_snapshot is not None:
        # If existing snapshot has no actual BSR value, treat it as stale
        # regardless of age — empty snapshots must not block fresh collection.
        if latest_snapshot.bsr_main is None and latest_snapshot.category_bsr_1 is None:
            pass  # stale empty snapshot, proceed to refresh
        else:
            latest_captured_at = latest_snapshot.captured_at
            if latest_captured_at.tzinfo is None:
                latest_captured_at = latest_captured_at.replace(tzinfo=UTC)
            age = now - latest_captured_at
            if age < timedelta(hours=min_hours_between_snapshots):
                rounded_hours = round(age.total_seconds() / 3600, 1)
                return (
                    "skipped",
                    latest_snapshot,
                    f"Latest snapshot is only {rounded_hours}h old.",
                )

    try:
        detail = collect_and_store_book_details(db, book)
    except Exception as exc:
        return "failed", latest_snapshot, str(exc)[:200]

    snapshot = None
    if detail.latest_bsr_snapshot is not None:
        snapshot = db.get(BSRSnapshot, detail.latest_bsr_snapshot.id)
    if snapshot is not None and (
        snapshot.bsr_main is not None
        or snapshot.category_bsr_1 is not None
        or snapshot.category_bsr_2 is not None
        or snapshot.category_bsr_3 is not None
    ):
        return "refreshed", snapshot, None
    # Delete empty snapshot to avoid inflating counts
    if snapshot is not None:
        db.delete(snapshot)
        db.flush()
    return "failed", None, "No BSR data found on detail page."
