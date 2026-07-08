from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.review import Review, ReviewCluster
from app.schemas.review_cluster import ReviewClusterRead
from app.services.ai_intelligence import cluster_reviews_semantically


def analyze_book_reviews(db: Session, book: Book) -> list[ReviewClusterRead]:
    reviews = list(
        db.scalars(
            select(Review)
            .where(Review.book_id == book.id)
            .order_by(Review.review_date.desc().nullslast(), Review.id.desc())
        )
    )
    if not reviews:
        return []

    db.execute(delete(ReviewCluster).where(ReviewCluster.book_id == book.id))
    db.flush()

    payloads, _ = cluster_reviews_semantically(reviews)
    created_clusters: list[ReviewCluster] = []
    for payload in payloads:
        cluster = ReviewCluster(book_id=book.id, **payload)
        db.add(cluster)
        created_clusters.append(cluster)

    db.commit()
    return [ReviewClusterRead.model_validate(cluster) for cluster in created_clusters]


def list_review_clusters_for_book(db: Session, book_id: int) -> list[ReviewClusterRead]:
    clusters = list(
        db.scalars(
            select(ReviewCluster)
            .where(ReviewCluster.book_id == book_id)
            .order_by(ReviewCluster.frequency.desc().nullslast(), ReviewCluster.id.asc())
        )
    )
    return [ReviewClusterRead.model_validate(cluster) for cluster in clusters]
