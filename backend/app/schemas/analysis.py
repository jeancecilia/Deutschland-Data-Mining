from pydantic import BaseModel, Field

from app.schemas.book import BookRead
from app.schemas.review_cluster import ReviewClusterRead
from app.schemas.signal import OpportunitySignalRead


class OpportunityScoreRead(BaseModel):
    keyword_specificity_score: int | None
    new_entrant_signal: int | None
    review_insight_score: int | None
    demand_score: int | None
    saturation_risk: int | None
    entry_feasibility_score: int | None
    review_wall_risk: int | None
    differentiation_score: int | None
    ai_slop_score: int | None
    brand_dominance_risk: int | None
    content_complexity_risk: int | None
    compliance_risk: int | None
    price_compression_risk: int | None
    authority_risk: int | None
    research_effort_score: int | None
    final_score: int | None
    explanation: str | None


class OpportunityAnalysisRead(BaseModel):
    niche_cluster_id: int
    niche_cluster_name: str
    main_keyword: str
    score: OpportunityScoreRead
    top_books: list[BookRead]


class BookClassInferenceRead(BaseModel):
    book_class: str
    confidence: int
    evidence: list[str]
    low_content_signal: int
    medium_content_signal: int
    high_content_signal: int
    sachbuch_signal: int


class ClusterKeywordRead(BaseModel):
    keyword: str
    relevance_score: int | None


class BSRMetricsRead(BaseModel):
    snapshot_count: int
    latest_bsr: int | None
    average_bsr: float | None
    median_bsr: float | None
    volatility: float | None
    trend: str
    stability: int | None
    improvement: int | None
    decay: int | None


class CompetitorBookRead(BaseModel):
    id: int
    asin: str
    title: str | None
    subtitle: str | None
    author: str | None
    publisher: str | None
    cover_url: str | None
    formats: str | None
    publication_date: str | None
    page_count: int | None
    description: str | None
    book_class: str | None
    relevance_score: int | None
    latest_price: float | None
    latest_rating: float | None
    latest_review_count: int | None
    latest_position: int | None
    latest_seen_at: str | None
    edition_info: str | None
    category_labels: list[str]
    listing_target_audience: str | None
    actual_target_audience: str | None
    listing_quality_score: int
    cover_quality_score: int
    freshness_score: int
    content_depth_score: int
    category_fit_score: int
    publication_age_years: float | None
    professional_publisher_signal: int
    series_signal: int
    sponsored_visibility: int
    search_observation_count: int
    review_growth: int | None
    review_trend: str
    table_of_contents_excerpt: str | None
    top_keywords: list[str]
    strengths: list[str]
    weaknesses: list[str]
    semantic_summary: str | None
    ai_target_audience: str | None
    ai_core_problem: str | None
    ai_use_case: str | None
    ai_promised_outcome: str | None
    ai_book_format: str | None
    ai_feature_terms: list[str]
    bsr: BSRMetricsRead


class CompetitorSummaryRead(BaseModel):
    publisher_concentration: int
    title_similarity: int
    low_review_visibility: int
    new_entrant_visibility: int
    ad_density: int
    series_presence: int
    professional_publisher_share: int
    strong_competitor_count: int
    weak_competitor_count: int
    average_review_count: float
    average_rating: float | None
    keyword_repetition: int
    bsr_snapshot_coverage: int
    average_listing_quality: int | None
    average_cover_quality: int | None
    average_freshness: int | None
    average_content_depth: int | None
    average_publication_age_years: float | None
    category_overlap_score: int | None


class KeywordStrategyRead(BaseModel):
    primary_keywords: list[str]
    secondary_keywords: list[str]
    long_tail_keywords: list[str]
    backend_keywords: list[str]
    avoid_keywords: list[str]
    keyword_clusters: list[str]


class CategoryStrategyRead(BaseModel):
    possible_categories: list[str]
    category_relevance: list[str]
    category_risks: list[str]
    visibility_opportunities: list[str]


class NicheClusterAnalysisRead(BaseModel):
    niche_cluster_id: int
    niche_cluster_name: str
    main_keyword: str
    keyword_count: int
    book_count: int
    top_keywords: list[ClusterKeywordRead]
    top_complaints: list[str]
    top_opportunities: list[str]
    positive_review_signals: list[str]
    missing_features: list[str]
    buyer_words: list[str]
    audience_hints: list[str]
    recommended_book_class: str | None
    book_classification: BookClassInferenceRead
    competitor_summary: CompetitorSummaryRead
    keyword_strategy: KeywordStrategyRead
    category_strategy: CategoryStrategyRead
    top_books: list[BookRead]
    competitor_books: list[CompetitorBookRead]
    review_insights: list[ReviewClusterRead]
    signals: list[OpportunitySignalRead] = Field(default_factory=list)
    score: OpportunityScoreRead
