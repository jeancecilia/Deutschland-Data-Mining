from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.signal import OpportunitySignalRead


class SachbuchTopicGapRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    niche_cluster_id: int
    topic_gap_summary: str | None
    outdated_content_signal: int | None
    missing_examples_signal: int | None
    missing_checklists_signal: int | None
    localization_gap_signal: int | None
    content_depth_score: int | None
    authority_required: bool
    expert_review_required: bool
    created_at: datetime
    updated_at: datetime


class SachbuchOpportunityScoreRead(BaseModel):
    german_demand_signal: int | None
    topic_gap_signal: int | None
    depth_weakness_signal: int | None
    freshness_need_signal: int | None
    localization_signal: int | None
    differentiation_signal: int | None
    evergreen_potential_signal: int | None
    monetization_potential_signal: int | None
    authority_risk: int | None
    research_effort_risk: int | None
    liability_risk: int | None
    update_risk: int | None
    publisher_dominance_risk: int | None
    review_wall_risk: int | None
    final_score: int | None
    explanation: str | None
    quality_warnings: list[str]


class SachbuchAnalysisRead(BaseModel):
    niche_cluster_id: int
    niche_cluster_name: str
    main_keyword: str
    opportunity_score: int | None
    sachbuch_score: SachbuchOpportunityScoreRead
    go_decision: str
    inferred_book_class: str
    book_class_confidence: int
    classification_evidence: list[str]
    recommended_target_audience: str
    reader_problem: str
    reader_promise: str
    why_now: str
    subtitle_ideas: list[str]
    positioning_angles: list[str]
    differentiation_opportunities: list[str]
    chapter_blueprint: list[str]
    subchapter_blueprint: list[str]
    practice_modules: list[str]
    checklist_ideas: list[str]
    case_study_ideas: list[str]
    glossary_terms: list[str]
    research_questions: list[str]
    backend_keywords: list[str]
    category_strategy: list[str]
    source_requirements: list[str]
    expert_needs: list[str]
    quality_warnings: list[str]
    cover_direction: list[str]
    target_length: str
    writing_effort: str
    topic_gap: SachbuchTopicGapRead
    signals: list[OpportunitySignalRead] = Field(default_factory=list)
