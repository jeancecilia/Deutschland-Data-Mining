from __future__ import annotations

from statistics import median

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.keyword import Keyword
from app.models.niche import NicheCluster, NicheClusterBook, NicheClusterKeyword, OpportunityScore
from app.models.review import ReviewCluster
from app.models.run import BSRSnapshot, SearchResult, SearchRun
from app.schemas.analysis import OpportunityAnalysisRead, OpportunityScoreRead
from app.schemas.book import BookRead
from app.services.book_classification import infer_book_class
from app.services.book_filters import is_probable_book_record
from app.services.scoring_engine import compute_opportunity_scorecard


def analyze_keyword_opportunity(db: Session, keyword: Keyword) -> OpportunityAnalysisRead:
    latest_run = db.scalars(
        select(SearchRun)
        .where(SearchRun.keyword_id == keyword.id, SearchRun.status == "completed")
        .order_by(SearchRun.run_at.desc())
    ).first()
    if latest_run is None:
        raise ValueError("No completed search run exists for this keyword.")

    result_rows = db.execute(
        select(SearchResult, Book)
        .join(Book, SearchResult.book_id == Book.id)
        .where(SearchResult.search_run_id == latest_run.id)
        .order_by(SearchResult.position.asc())
    ).all()
    result_rows = [(result, book) for result, book in result_rows if is_probable_book_record(book)]
    if not result_rows:
        raise ValueError("No book-like search results are stored for this keyword.")

    books = [book for _, book in result_rows]
    top_results = result_rows[:10]
    top_book_ids = [book.id for _, book in top_results]
    seed_id = keyword.seed_keyword_id or keyword.id
    related_keyword_count = len(
        list(
            db.scalars(
                select(Keyword.id).where(
                    (Keyword.id == seed_id) | (Keyword.seed_keyword_id == seed_id)
                )
            )
        )
    )
    review_counts = [result.review_count or 0 for result, _ in top_results]
    median_review_count = median(review_counts) if review_counts else 0
    review_clusters = (
        list(
            db.scalars(
                select(ReviewCluster)
                .where(ReviewCluster.book_id.in_(top_book_ids))
                .order_by(ReviewCluster.frequency.desc().nullslast(), ReviewCluster.id.asc())
            )
        )
        if top_book_ids
        else []
    )
    bsr_snapshots = (
        list(
            db.scalars(
                select(BSRSnapshot)
                .where(BSRSnapshot.book_id.in_(top_book_ids))
                .order_by(BSRSnapshot.book_id.asc(), BSRSnapshot.captured_at.asc(), BSRSnapshot.id.asc())
            )
        )
        if top_book_ids
        else []
    )
    bsr_histories_by_book: dict[int, list[int]] = {}
    for snapshot in bsr_snapshots:
        if snapshot.bsr_main is None:
            continue
        bsr_histories_by_book.setdefault(snapshot.book_id, []).append(snapshot.bsr_main)
    class_inference = infer_book_class(
        keyword.keyword,
        books[:12],
        review_clusters,
        declared_book_type=keyword.book_type,
    )

    scorecard = compute_opportunity_scorecard(
        keyword_text=keyword.keyword,
        book_type=class_inference.book_class,
        related_keyword_count=related_keyword_count,
        visible_result_count=latest_run.result_count or len(result_rows),
        top_review_counts=review_counts,
        top_ratings=[float(result.rating) for result, _ in top_results if result.rating is not None],
        top_prices=[float(result.price) for result, _ in top_results if result.price is not None],
        top_positions=[result.position for result, _ in top_results],
        top_titles=[book.title or "" for _, book in top_results],
        top_publishers=[book.publisher or "" for _, book in top_results],
        review_clusters=review_clusters,
        bsr_histories=[bsr_histories_by_book.get(book.id, []) for _, book in top_results],
    )

    explanation = (
        f"Latest run captured {latest_run.result_count or len(result_rows)} visible books across "
        f"{related_keyword_count} related keywords. Top-10 median review count is {int(median_review_count)}. "
        f"Inferred class is {class_inference.book_class} at confidence {class_inference.confidence}. "
        f"{scorecard.explanation}"
    )

    niche_cluster = _upsert_niche_cluster(db, keyword, books)
    niche_cluster.book_class = class_inference.book_class
    if not keyword.book_type:
        keyword.book_type = class_inference.book_class
    score = OpportunityScore(
        niche_cluster_id=niche_cluster.id,
        keyword_specificity_score=scorecard.keyword_specificity_score,
        new_entrant_signal=scorecard.new_entrant_signal,
        review_insight_score=scorecard.review_insight_score,
        demand_score=scorecard.demand_score,
        saturation_risk=scorecard.saturation_risk,
        entry_feasibility_score=scorecard.entry_feasibility_score,
        review_wall_risk=scorecard.review_wall_risk,
        differentiation_score=scorecard.differentiation_score,
        ai_slop_score=scorecard.ai_slop_score,
        brand_dominance_risk=scorecard.brand_dominance_risk,
        content_complexity_risk=scorecard.content_complexity_risk,
        compliance_risk=scorecard.compliance_risk,
        price_compression_risk=scorecard.price_compression_risk,
        authority_risk=scorecard.authority_risk,
        research_effort_score=scorecard.research_effort_score,
        final_score=scorecard.final_score,
        explanation=explanation,
    )
    db.add(score)
    db.commit()
    db.refresh(score)

    return OpportunityAnalysisRead(
        niche_cluster_id=niche_cluster.id,
        niche_cluster_name=niche_cluster.name,
        main_keyword=keyword.keyword,
        score=OpportunityScoreRead(
            keyword_specificity_score=score.keyword_specificity_score,
            new_entrant_signal=score.new_entrant_signal,
            review_insight_score=score.review_insight_score,
            demand_score=score.demand_score,
            saturation_risk=score.saturation_risk,
            entry_feasibility_score=score.entry_feasibility_score,
            review_wall_risk=score.review_wall_risk,
            differentiation_score=score.differentiation_score,
            ai_slop_score=score.ai_slop_score,
            brand_dominance_risk=score.brand_dominance_risk,
            content_complexity_risk=score.content_complexity_risk,
            compliance_risk=score.compliance_risk,
            price_compression_risk=score.price_compression_risk,
            authority_risk=score.authority_risk,
            research_effort_score=score.research_effort_score,
            final_score=score.final_score,
            explanation=score.explanation,
        ),
        top_books=[BookRead.model_validate(book) for _, book in top_results],
    )


def _upsert_niche_cluster(db: Session, keyword: Keyword, books: list[Book]) -> NicheCluster:
    niche_cluster = db.scalars(
        select(NicheCluster).where(
            NicheCluster.main_keyword == keyword.keyword,
            NicheCluster.marketplace == keyword.marketplace,
            NicheCluster.language == keyword.language,
        )
    ).first()

    if niche_cluster is None:
        niche_cluster = NicheCluster(
            name=keyword.keyword,
            description=f"Auto-generated cluster for keyword {keyword.keyword}",
            marketplace=keyword.marketplace,
            language=keyword.language,
            main_keyword=keyword.keyword,
            book_class=keyword.book_type,
            status="analyzed",
        )
        db.add(niche_cluster)
        db.flush()
    else:
        niche_cluster.status = "analyzed"
        niche_cluster.book_class = keyword.book_type

    existing_keyword_link = db.scalars(
        select(NicheClusterKeyword).where(
            NicheClusterKeyword.niche_cluster_id == niche_cluster.id,
            NicheClusterKeyword.keyword_id == keyword.id,
        )
    ).first()
    if existing_keyword_link is None:
        db.add(
            NicheClusterKeyword(
                niche_cluster_id=niche_cluster.id,
                keyword_id=keyword.id,
                relevance_score=100,
            )
        )

    db.execute(delete(NicheClusterBook).where(NicheClusterBook.niche_cluster_id == niche_cluster.id))
    db.flush()
    for index, book in enumerate(books, start=1):
        relevance = max(1, 100 - (index - 1) * 4)
        db.add(
            NicheClusterBook(
                niche_cluster_id=niche_cluster.id,
                book_id=book.id,
                relevance_score=relevance,
            )
        )
    db.flush()
    return niche_cluster
