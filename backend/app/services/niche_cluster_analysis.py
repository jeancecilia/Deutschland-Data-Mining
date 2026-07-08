from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean, median

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.keyword import Keyword
from app.models.niche import NicheCluster, NicheClusterBook, NicheClusterKeyword, OpportunityScore
from app.models.review import Review, ReviewCluster
from app.models.run import BSRSnapshot, SearchResult, SearchRun
from app.schemas.analysis import (
    BSRMetricsRead,
    BookClassInferenceRead,
    CategoryStrategyRead,
    ClusterKeywordRead,
    CompetitorBookRead,
    CompetitorSummaryRead,
    KeywordStrategyRead,
    NicheClusterAnalysisRead,
    OpportunityScoreRead,
)
from app.schemas.book import BookRead
from app.schemas.review_cluster import ReviewClusterRead
from app.services.book_classification import infer_book_class
from app.services.book_filters import is_probable_book_record
from app.services.market_intelligence import build_competitor_profile
from app.services.scoring_engine import clamp as _clamp, compute_opportunity_scorecard
from app.services.signal_generation import build_cluster_signals
from app.services.text_utils import normalize_text


GERMAN_STOPWORDS = {
    "aber",
    "alle",
    "auch",
    "auf",
    "aus",
    "bei",
    "das",
    "dass",
    "dem",
    "den",
    "der",
    "des",
    "die",
    "eine",
    "einem",
    "einen",
    "einer",
    "eines",
    "einfach",
    "fuer",
    "für",
    "ganz",
    "hat",
    "habe",
    "haben",
    "hier",
    "ich",
    "ihre",
    "ihren",
    "immer",
    "kein",
    "keine",
    "kann",
    "mehr",
    "mein",
    "mit",
    "nach",
    "nicht",
    "noch",
    "oder",
    "schon",
    "sehr",
    "sich",
    "sind",
    "ueber",
    "über",
    "und",
    "viel",
    "vom",
    "von",
    "vor",
    "war",
    "weil",
    "wenn",
    "wie",
    "wird",
    "wirklich",
    "zum",
    "zur",
}


def build_and_analyze_seed_cluster(db: Session, seed_keyword: Keyword) -> NicheClusterAnalysisRead:
    related_keywords = _get_related_keywords(db, seed_keyword)
    related_keyword_ids = [keyword.id for keyword in related_keywords]

    runs = list(
        db.scalars(
            select(SearchRun)
            .where(SearchRun.keyword_id.in_(related_keyword_ids), SearchRun.status == "completed")
            .order_by(SearchRun.run_at.desc())
        )
    )
    if not runs:
        raise ValueError("No completed search runs exist for this seed keyword or its expansions.")

    latest_run_by_keyword: dict[int, SearchRun] = {}
    for run in runs:
        latest_run_by_keyword.setdefault(run.keyword_id, run)

    selected_run_ids = [run.id for run in latest_run_by_keyword.values()]
    result_rows = db.execute(
        select(SearchResult, Book)
        .join(Book, SearchResult.book_id == Book.id)
        .where(SearchResult.search_run_id.in_(selected_run_ids))
        .order_by(SearchResult.position.asc())
    ).all()
    result_rows = [(result, book) for result, book in result_rows if is_probable_book_record(book)]
    if not result_rows:
        raise ValueError("No book-like search results are stored for the related keyword space.")

    book_stats: dict[int, dict[str, object]] = defaultdict(lambda: {
        "book": None,
        "appearances": 0,
        "best_position": 999,
        "prices": [],
        "review_counts": [],
        "ratings": [],
    })
    for result, book in result_rows:
        stats = book_stats[book.id]
        stats["book"] = book
        stats["appearances"] = int(stats["appearances"]) + 1
        stats["best_position"] = min(int(stats["best_position"]), result.position)
        if result.price is not None:
            cast_prices = stats["prices"]
            assert isinstance(cast_prices, list)
            cast_prices.append(float(result.price))
        if result.review_count is not None:
            cast_list = stats["review_counts"]
            assert isinstance(cast_list, list)
            cast_list.append(result.review_count)
        if result.rating is not None:
            cast_ratings = stats["ratings"]
            assert isinstance(cast_ratings, list)
            cast_ratings.append(result.rating)

    ranked_books = sorted(
        book_stats.values(),
        key=lambda item: (-int(item["appearances"]), int(item["best_position"])),
    )
    top_ranked_books = ranked_books[:15]

    niche_cluster = _upsert_seed_cluster(db, seed_keyword, related_keywords, ranked_books)

    top_review_counts = [
        int(mean(stats["review_counts"])) if stats["review_counts"] else 0
        for stats in top_ranked_books[:10]
    ]
    top_ratings = [
        float(mean(stats["ratings"])) for stats in top_ranked_books[:10] if stats["ratings"]
    ]
    median_review_count = median(top_review_counts) if top_review_counts else 0
    top_book_ids = [int(cast["book"].id) for cast in top_ranked_books if cast["book"] is not None]

    review_cluster_rows = list(
        db.scalars(
            select(ReviewCluster)
            .where(
                ReviewCluster.book_id.in_(top_book_ids)
            )
            .order_by(ReviewCluster.frequency.desc().nullslast(), ReviewCluster.id.asc())
        )
    ) if top_book_ids else []
    class_inference = infer_book_class(
        seed_keyword.keyword,
        [stats["book"] for stats in top_ranked_books if stats["book"] is not None],
        review_cluster_rows,
        declared_book_type=seed_keyword.book_type,
    )
    niche_cluster.book_class = class_inference.book_class
    bsr_snapshots = list(
        db.scalars(
            select(BSRSnapshot)
            .where(BSRSnapshot.book_id.in_(top_book_ids))
            .order_by(BSRSnapshot.book_id.asc(), BSRSnapshot.captured_at.asc(), BSRSnapshot.id.asc())
        )
    ) if top_book_ids else []
    bsr_histories_by_book: dict[int, list[int]] = {}
    for snapshot in bsr_snapshots:
        if snapshot.bsr_main is None:
            continue
        bsr_histories_by_book.setdefault(snapshot.book_id, []).append(snapshot.bsr_main)

    scorecard = compute_opportunity_scorecard(
        keyword_text=seed_keyword.keyword,
        book_type=class_inference.book_class,
        related_keyword_count=len(related_keywords),
        visible_result_count=len(ranked_books),
        top_review_counts=top_review_counts,
        top_ratings=top_ratings,
        top_prices=[
            float(mean(stats["prices"]))
            for stats in top_ranked_books[:10]
            if stats["prices"]
        ],
        top_positions=[int(stats["best_position"]) for stats in top_ranked_books[:10]],
        top_titles=[
            (stats["book"].title or "") if stats["book"] is not None else ""
            for stats in top_ranked_books[:10]
        ],
        top_publishers=[
            (stats["book"].publisher or "") if stats["book"] is not None else ""
            for stats in top_ranked_books[:10]
        ],
        review_clusters=review_cluster_rows,
        bsr_histories=[
            bsr_histories_by_book.get(int(stats["book"].id), [])
            for stats in top_ranked_books[:10]
            if stats["book"] is not None
        ],
    )

    explanation = (
        f"Cluster uses {len(related_keywords)} related keywords and {len(ranked_books)} unique books from the latest runs. "
        f"Top-book median review count is {int(median_review_count)}. "
        f"Inferred class is {class_inference.book_class} at confidence {class_inference.confidence}. "
        f"{scorecard.explanation}"
    )

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

    return get_cluster_analysis(db, niche_cluster.id)


def get_cluster_analysis(db: Session, cluster_id: int) -> NicheClusterAnalysisRead:
    cluster = db.get(NicheCluster, cluster_id)
    if cluster is None:
        raise ValueError("Cluster not found.")

    latest_score = db.scalars(
        select(OpportunityScore)
        .where(OpportunityScore.niche_cluster_id == cluster.id)
        .order_by(OpportunityScore.created_at.desc(), OpportunityScore.id.desc())
    ).first()
    if latest_score is None:
        raise ValueError("Cluster has no stored score.")

    keyword_rows = db.execute(
        select(NicheClusterKeyword, Keyword)
        .join(Keyword, NicheClusterKeyword.keyword_id == Keyword.id)
        .where(NicheClusterKeyword.niche_cluster_id == cluster.id)
        .order_by(NicheClusterKeyword.relevance_score.desc().nullslast(), Keyword.id.asc())
    ).all()
    book_rows = db.execute(
        select(NicheClusterBook, Book)
        .join(Book, NicheClusterBook.book_id == Book.id)
        .where(NicheClusterBook.niche_cluster_id == cluster.id)
        .order_by(NicheClusterBook.relevance_score.desc().nullslast(), Book.id.asc())
    ).all()
    book_rows = [(link, book) for link, book in book_rows if is_probable_book_record(book)]
    book_ids = [book.id for _, book in book_rows]
    review_rows = list(
        db.scalars(
            select(Review)
            .where(Review.book_id.in_(book_ids))
            .order_by(Review.helpful_count.desc().nullslast(), Review.review_date.desc().nullslast(), Review.id.asc())
        )
    ) if book_ids else []
    review_cluster_rows = list(
        db.scalars(
            select(ReviewCluster)
            .where(ReviewCluster.book_id.in_(book_ids))
            .order_by(ReviewCluster.frequency.desc().nullslast(), ReviewCluster.id.asc())
        )
    ) if book_ids else []
    class_inference = infer_book_class(
        cluster.main_keyword or cluster.name,
        [book for _, book in book_rows[:15]],
        review_cluster_rows,
        declared_book_type=cluster.book_class,
    )

    top_keywords = [
        ClusterKeywordRead(keyword=keyword.keyword, relevance_score=link.relevance_score)
        for link, keyword in keyword_rows[:12]
    ]
    top_keyword_terms = [keyword.keyword for _, keyword in keyword_rows[:8]]
    top_books_payload = [BookRead.model_validate(book) for _, book in book_rows[:10]]
    competitor_books = [
        _build_competitor_book_snapshot(db, book, link.relevance_score, top_keyword_terms)
        for link, book in book_rows[:10]
    ]
    competitor_summary = _build_competitor_summary(
        top_keyword_terms,
        competitor_books,
    )

    negative_review_clusters = [cluster_row for cluster_row in review_cluster_rows if cluster_row.sentiment != "positive"]
    top_complaints = _unique_non_empty(
        [
            cluster_row.summary or cluster_row.cluster_name
            for cluster_row in negative_review_clusters[:8]
        ]
    )[:5]
    top_opportunities = _unique_non_empty(
        [
            cluster_row.suggested_improvements or cluster_row.summary or cluster_row.cluster_name
            for cluster_row in negative_review_clusters[:8]
        ]
    )[:5]
    positive_review_signals = _positive_review_signals(review_cluster_rows)
    missing_features = _missing_features(review_cluster_rows)
    buyer_words = _buyer_words(review_rows, review_cluster_rows)
    audience_hints = _audience_hints(competitor_books)
    keyword_strategy = _build_keyword_strategy(cluster.main_keyword or cluster.name, top_keyword_terms, competitor_books)
    category_strategy = _build_category_strategy(cluster.main_keyword or cluster.name, competitor_books, competitor_summary)
    review_insights = [ReviewClusterRead.model_validate(cluster_row) for cluster_row in review_cluster_rows[:12]]

    analysis = NicheClusterAnalysisRead(
        niche_cluster_id=cluster.id,
        niche_cluster_name=cluster.name,
        main_keyword=cluster.main_keyword or cluster.name,
        keyword_count=len(keyword_rows),
        book_count=len(book_rows),
        top_keywords=top_keywords,
        top_complaints=top_complaints,
        top_opportunities=top_opportunities,
        positive_review_signals=positive_review_signals,
        missing_features=missing_features,
        buyer_words=buyer_words,
        audience_hints=audience_hints,
        recommended_book_class=class_inference.book_class,
        book_classification=BookClassInferenceRead(
            book_class=class_inference.book_class,
            confidence=class_inference.confidence,
            evidence=class_inference.evidence,
            low_content_signal=class_inference.low_content_signal,
            medium_content_signal=class_inference.medium_content_signal,
            high_content_signal=class_inference.high_content_signal,
            sachbuch_signal=class_inference.sachbuch_signal,
        ),
        competitor_summary=competitor_summary,
        keyword_strategy=keyword_strategy,
        category_strategy=category_strategy,
        top_books=top_books_payload,
        competitor_books=competitor_books,
        review_insights=review_insights,
        score=OpportunityScoreRead(
            keyword_specificity_score=latest_score.keyword_specificity_score,
            new_entrant_signal=latest_score.new_entrant_signal,
            review_insight_score=latest_score.review_insight_score,
            demand_score=latest_score.demand_score,
            saturation_risk=latest_score.saturation_risk,
            entry_feasibility_score=latest_score.entry_feasibility_score,
            review_wall_risk=latest_score.review_wall_risk,
            differentiation_score=latest_score.differentiation_score,
            ai_slop_score=latest_score.ai_slop_score,
            brand_dominance_risk=latest_score.brand_dominance_risk,
            content_complexity_risk=latest_score.content_complexity_risk,
            compliance_risk=latest_score.compliance_risk,
            price_compression_risk=latest_score.price_compression_risk,
            authority_risk=latest_score.authority_risk,
            research_effort_score=latest_score.research_effort_score,
            final_score=latest_score.final_score,
            explanation=latest_score.explanation,
        ),
    )
    return analysis.model_copy(update={"signals": build_cluster_signals(analysis)})


def _get_related_keywords(db: Session, seed_keyword: Keyword) -> list[Keyword]:
    seed_id = seed_keyword.seed_keyword_id or seed_keyword.id
    return list(
        db.scalars(
            select(Keyword)
            .where((Keyword.id == seed_id) | (Keyword.seed_keyword_id == seed_id))
            .order_by(Keyword.id.asc())
        )
    )


def _upsert_seed_cluster(
    db: Session,
    seed_keyword: Keyword,
    related_keywords: list[Keyword],
    ranked_books: list[dict[str, object]],
) -> NicheCluster:
    niche_cluster = db.scalars(
        select(NicheCluster).where(
            NicheCluster.main_keyword == seed_keyword.keyword,
            NicheCluster.marketplace == seed_keyword.marketplace,
            NicheCluster.language == seed_keyword.language,
        )
    ).first()

    if niche_cluster is None:
        niche_cluster = NicheCluster(
            name=seed_keyword.keyword,
            description=f"Aggregated niche cluster for seed keyword {seed_keyword.keyword}",
            marketplace=seed_keyword.marketplace,
            language=seed_keyword.language,
            main_keyword=seed_keyword.keyword,
            book_class=seed_keyword.book_type,
            status="clustered",
        )
        db.add(niche_cluster)
        db.flush()
    else:
        niche_cluster.status = "clustered"
        niche_cluster.book_class = seed_keyword.book_type

    db.execute(delete(NicheClusterKeyword).where(NicheClusterKeyword.niche_cluster_id == niche_cluster.id))
    db.execute(delete(NicheClusterBook).where(NicheClusterBook.niche_cluster_id == niche_cluster.id))
    db.flush()

    for keyword in related_keywords:
        relevance = 100 if keyword.id == seed_keyword.id else 70
        db.add(
            NicheClusterKeyword(
                niche_cluster_id=niche_cluster.id,
                keyword_id=keyword.id,
                relevance_score=relevance,
            )
        )

    for stats in ranked_books:
        book = stats["book"]
        if book is None:
            continue
        appearances = int(stats["appearances"])
        best_position = int(stats["best_position"])
        relevance = _clamp(appearances * 20 + max(0, 40 - best_position * 2))
        db.add(
            NicheClusterBook(
                niche_cluster_id=niche_cluster.id,
                book_id=book.id,
                relevance_score=relevance,
            )
        )

    db.flush()
    return niche_cluster


def _build_competitor_book_snapshot(
    db: Session,
    book: Book,
    relevance_score: int | None,
    cluster_keywords: list[str],
) -> CompetitorBookRead:
    latest_result = db.scalars(
        select(SearchResult)
        .where(SearchResult.book_id == book.id)
        .order_by(SearchResult.captured_at.desc(), SearchResult.id.desc())
    ).first()
    search_result_history = list(
        db.scalars(
            select(SearchResult)
            .where(SearchResult.book_id == book.id)
            .order_by(SearchResult.captured_at.asc(), SearchResult.id.asc())
        )
    )
    bsr_snapshots = list(
        db.scalars(
            select(BSRSnapshot)
            .where(BSRSnapshot.book_id == book.id)
            .order_by(BSRSnapshot.captured_at.asc(), BSRSnapshot.id.asc())
        )
    )
    review_clusters = list(
        db.scalars(
            select(ReviewCluster)
            .where(ReviewCluster.book_id == book.id)
            .order_by(ReviewCluster.frequency.desc().nullslast(), ReviewCluster.id.asc())
        )
    )
    profile = build_competitor_profile(" ".join(cluster_keywords), book, review_clusters)

    matched_keywords = [
        keyword
        for keyword in cluster_keywords
        if keyword.casefold() in ((book.title or "").casefold() + " " + (book.subtitle or "").casefold())
    ]
    top_keywords = matched_keywords[:4] or cluster_keywords[:4]
    strengths = _unique_non_empty([cluster.summary or cluster.cluster_name for cluster in review_clusters if cluster.sentiment == "positive"])[:3]
    weaknesses = _unique_non_empty([cluster.summary or cluster.cluster_name for cluster in review_clusters if cluster.sentiment != "positive"])[:3]
    review_history = [result.review_count for result in search_result_history if result.review_count is not None]
    review_growth = review_history[-1] - review_history[0] if len(review_history) >= 2 else None
    review_trend = "unknown"
    if review_growth is not None:
        if review_growth >= 10:
            review_trend = "growing"
        elif review_growth <= -5:
            review_trend = "falling"
        else:
            review_trend = "flat"
    sponsored_hits = sum(1 for result in search_result_history if result.is_sponsored)
    sponsored_visibility = _clamp(round((sponsored_hits / max(1, len(search_result_history))) * 100)) if search_result_history else 0

    return CompetitorBookRead(
        id=book.id,
        asin=book.asin,
        title=book.title,
        subtitle=book.subtitle,
        author=book.author,
        publisher=book.publisher,
        cover_url=book.cover_url,
        formats=book.formats,
        publication_date=book.publication_date.isoformat() if book.publication_date else None,
        page_count=book.page_count,
        description=book.description,
        book_class=book.book_class,
        relevance_score=relevance_score,
        latest_price=float(latest_result.price) if latest_result and latest_result.price is not None else None,
        latest_rating=latest_result.rating if latest_result else None,
        latest_review_count=latest_result.review_count if latest_result else None,
        latest_position=latest_result.position if latest_result else None,
        latest_seen_at=latest_result.captured_at.isoformat() if latest_result else None,
        edition_info=profile.edition_info,
        category_labels=profile.category_labels,
        listing_target_audience=profile.listing_target_audience,
        actual_target_audience=profile.actual_target_audience,
        listing_quality_score=profile.listing_quality_score,
        cover_quality_score=profile.cover_quality_score,
        freshness_score=profile.freshness_score,
        content_depth_score=profile.content_depth_score,
        category_fit_score=profile.category_fit_score,
        publication_age_years=profile.publication_age_years,
        professional_publisher_signal=profile.professional_publisher_signal,
        series_signal=profile.series_signal,
        sponsored_visibility=sponsored_visibility,
        search_observation_count=len(search_result_history),
        review_growth=review_growth,
        review_trend=review_trend,
        table_of_contents_excerpt=profile.table_of_contents_excerpt,
        top_keywords=top_keywords,
        strengths=strengths,
        weaknesses=weaknesses,
        semantic_summary=profile.semantic_summary,
        ai_target_audience=profile.ai_target_audience,
        ai_core_problem=profile.ai_core_problem,
        ai_use_case=profile.ai_use_case,
        ai_promised_outcome=profile.ai_promised_outcome,
        ai_book_format=profile.ai_book_format,
        ai_feature_terms=profile.ai_feature_terms,
        bsr=_build_bsr_metrics(bsr_snapshots),
    )


def _build_bsr_metrics(snapshots: list[BSRSnapshot]) -> BSRMetricsRead:
    bsr_values = [snapshot.bsr_main for snapshot in snapshots if snapshot.bsr_main is not None]
    if not bsr_values:
        return BSRMetricsRead(
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

    first_value = bsr_values[0]
    last_value = bsr_values[-1]
    max_value = max(bsr_values)
    min_value = min(bsr_values)
    volatility = round(((max_value - min_value) / max_value) * 100, 2) if max_value else 0.0
    delta = last_value - first_value
    if delta <= -max(100, round(first_value * 0.05)):
        trend = "improving"
    elif delta >= max(100, round(first_value * 0.05)):
        trend = "decaying"
    else:
        trend = "stable"

    return BSRMetricsRead(
        snapshot_count=len(snapshots),
        latest_bsr=last_value,
        average_bsr=round(mean(bsr_values), 2),
        median_bsr=round(median(bsr_values), 2),
        volatility=volatility,
        trend=trend,
        stability=_clamp(round(100 - min(100, volatility))),
        improvement=max(0, first_value - last_value),
        decay=max(0, last_value - first_value),
    )


def _unique_non_empty(values: list[str | None]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = (value or "").strip()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _build_competitor_summary(
    cluster_keywords: list[str],
    competitor_books: list[CompetitorBookRead],
) -> CompetitorSummaryRead:
    publisher_counts: dict[str, int] = {}
    title_tokens: list[set[str]] = []
    review_counts = [book.latest_review_count or 0 for book in competitor_books]
    ratings = [book.latest_rating for book in competitor_books if book.latest_rating is not None]
    repeated_keyword_hits = 0
    books_with_snapshots = 0
    category_counts: dict[str, int] = {}
    publication_ages = [book.publication_age_years for book in competitor_books if book.publication_age_years is not None]

    for book in competitor_books:
        publisher = (book.publisher or "unknown").strip().casefold()
        publisher_counts[publisher] = publisher_counts.get(publisher, 0) + 1
        title_text = (book.title or "").casefold()
        title_tokens.append({token for token in title_text.replace(":", " ").split() if len(token) > 3})
        repeated_keyword_hits += sum(1 for keyword in cluster_keywords if keyword.casefold() in title_text)
        if book.bsr.snapshot_count > 0:
            books_with_snapshots += 1
        for category in book.category_labels:
            normalized = category.casefold()
            category_counts[normalized] = category_counts.get(normalized, 0) + 1

    max_publisher_share = max(publisher_counts.values(), default=0)
    publisher_concentration = _clamp(round((max_publisher_share / max(1, len(competitor_books))) * 100))
    pair_scores: list[float] = []
    for index, tokens in enumerate(title_tokens):
        for compare_tokens in title_tokens[index + 1:]:
            if not tokens or not compare_tokens:
                continue
            overlap = len(tokens & compare_tokens)
            union = len(tokens | compare_tokens)
            if union:
                pair_scores.append((overlap / union) * 100)
    title_similarity = _clamp(round(mean(pair_scores))) if pair_scores else 0

    low_review_visibility = sum(1 for count in review_counts if 0 < count <= 100)
    new_entrant_visibility = sum(1 for count in review_counts if 0 < count <= 30)
    strong_competitor_count = sum(1 for count in review_counts if count >= 300)
    weak_competitor_count = sum(1 for count in review_counts if count <= 20)
    max_category_share = max(category_counts.values(), default=0)

    return CompetitorSummaryRead(
        publisher_concentration=publisher_concentration,
        title_similarity=title_similarity,
        low_review_visibility=low_review_visibility,
        new_entrant_visibility=new_entrant_visibility,
        ad_density=_clamp(round(mean([book.sponsored_visibility for book in competitor_books]))) if competitor_books else 0,
        series_presence=_clamp(round(mean([book.series_signal for book in competitor_books]))) if competitor_books else 0,
        professional_publisher_share=_clamp(round(mean([book.professional_publisher_signal for book in competitor_books]))) if competitor_books else 0,
        strong_competitor_count=strong_competitor_count,
        weak_competitor_count=weak_competitor_count,
        average_review_count=round(mean(review_counts), 2) if review_counts else 0.0,
        average_rating=round(mean(ratings), 2) if ratings else None,
        keyword_repetition=repeated_keyword_hits,
        bsr_snapshot_coverage=_clamp(round((books_with_snapshots / max(1, len(competitor_books))) * 100)),
        average_listing_quality=_clamp(round(mean([book.listing_quality_score for book in competitor_books]))) if competitor_books else None,
        average_cover_quality=_clamp(round(mean([book.cover_quality_score for book in competitor_books]))) if competitor_books else None,
        average_freshness=_clamp(round(mean([book.freshness_score for book in competitor_books]))) if competitor_books else None,
        average_content_depth=_clamp(round(mean([book.content_depth_score for book in competitor_books]))) if competitor_books else None,
        average_publication_age_years=round(mean(publication_ages), 2) if publication_ages else None,
        category_overlap_score=_clamp(round((max_category_share / max(1, len(competitor_books))) * 100)) if category_counts else None,
    )


def _positive_review_signals(review_clusters: list[ReviewCluster]) -> list[str]:
    return _unique_non_empty(
        [
            normalize_text(cluster.summary) or normalize_text(cluster.cluster_name)
            for cluster in review_clusters
            if cluster.sentiment == "positive" or cluster.cluster_type == "praise"
        ]
    )[:5]


def _missing_features(review_clusters: list[ReviewCluster]) -> list[str]:
    return _unique_non_empty(
        [
            normalize_text(cluster.missing_feature)
            or normalize_text(cluster.suggested_improvements)
            or normalize_text(cluster.summary)
            or normalize_text(cluster.cluster_name)
            for cluster in review_clusters
            if cluster.sentiment != "positive" or cluster.cluster_type == "missing_feature"
        ]
    )[:6]


def _buyer_words(review_rows: list[Review], review_clusters: list[ReviewCluster]) -> list[str]:
    counts: Counter[str] = Counter()
    corpora = [
        " ".join(part for part in [review.title, review.body] if part)
        for review in review_rows[:60]
    ]
    corpora.extend(
        " ".join(part for part in [cluster.cluster_name, cluster.summary, cluster.example_snippets] if part)
        for cluster in review_clusters[:20]
    )
    for cluster in review_clusters[:20]:
        for word in cluster.buyer_words or []:
            counts[word.casefold()] += 3
    for corpus in corpora:
        normalized = (normalize_text(corpus) or "").casefold()
        for token in normalized.replace("/", " ").replace("-", " ").split():
            if len(token) < 4 or len(token) > 24 or token in GERMAN_STOPWORDS:
                continue
            if not any(character.isalpha() for character in token):
                continue
            counts[token] += 1
    return [token for token, _ in counts.most_common(8)]


def _audience_hints(competitor_books: list[CompetitorBookRead]) -> list[str]:
    return _unique_non_empty(
        [
            normalize_text(book.ai_target_audience)
            or normalize_text(book.actual_target_audience)
            or normalize_text(book.listing_target_audience)
            for book in competitor_books
        ]
    )[:5]


def _build_keyword_strategy(
    main_keyword: str,
    top_keyword_terms: list[str],
    competitor_books: list[CompetitorBookRead],
) -> KeywordStrategyRead:
    normalized_main = normalize_text(main_keyword) or main_keyword
    keyword_pool = _unique_non_empty(
        [
            normalized_main,
            *top_keyword_terms,
            *[keyword for book in competitor_books for keyword in book.top_keywords],
            *[term for book in competitor_books for term in book.ai_feature_terms],
        ]
    )
    long_tail_keywords = [keyword for keyword in keyword_pool if len(keyword.split()) >= 3][:6]
    avoid_keywords = _unique_non_empty(
        [
            "allgemein",
            "komplett",
            "ultimativ",
            "buch" if any(keyword.casefold() == "buch" for keyword in keyword_pool) else None,
        ]
    )[:5]
    return KeywordStrategyRead(
        primary_keywords=keyword_pool[:3],
        secondary_keywords=keyword_pool[3:8],
        long_tail_keywords=long_tail_keywords,
        backend_keywords=_generic_backend_keywords(normalized_main, keyword_pool),
        avoid_keywords=avoid_keywords,
        keyword_clusters=_keyword_clusters(keyword_pool),
    )


def _build_category_strategy(
    main_keyword: str,
    competitor_books: list[CompetitorBookRead],
    competitor_summary: CompetitorSummaryRead,
) -> CategoryStrategyRead:
    categories = _unique_non_empty(
        [category for book in competitor_books for category in book.category_labels]
    )[:8]
    relevance = [
        f"Kernkategorie eng an '{normalize_text(main_keyword) or main_keyword}' ausrichten.",
        f"Sichtbare Wettbewerbskategorien: {', '.join(categories[:4]) if categories else 'noch unvollständig extrahiert'}.",
    ]
    risks = ["Zu breite Allgemein-Kategorien schwächen die Differenzierung im Ranking."]
    if (competitor_summary.category_overlap_score or 0) >= 60:
        risks.append("Hohe Kategorie-Überlappung deutet auf dichte Wettbewerbscluster hin.")
    visibility = [
        "Sekundärkategorie mit Praxis- oder Zielgruppenbezug wählen.",
        "Schwächere Listing-Qualität im sichtbaren Wettbewerbsumfeld als Sichtbarkeitshebel nutzen.",
    ]
    return CategoryStrategyRead(
        possible_categories=categories,
        category_relevance=relevance[:4],
        category_risks=risks[:4],
        visibility_opportunities=visibility[:4],
    )


def _generic_backend_keywords(main_keyword: str, keyword_pool: list[str]) -> list[str]:
    suggestions = [
        main_keyword,
        f"{main_keyword} ratgeber",
        f"{main_keyword} praxis",
        f"{main_keyword} vorlagen",
        f"{main_keyword} checklisten",
        *keyword_pool[:4],
    ]
    return _unique_non_empty(suggestions)[:8]


def _keyword_clusters(keyword_pool: list[str]) -> list[str]:
    clusters: list[str] = []
    for keyword in keyword_pool[:8]:
        first_token = keyword.split()[0] if keyword.split() else keyword
        if not first_token:
            continue
        clusters.append(f"{first_token}: {keyword}")
    return _unique_non_empty(clusters)[:6]
