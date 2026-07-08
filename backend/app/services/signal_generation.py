from __future__ import annotations

from app.models.discovery import DiscoveryCandidate
from app.schemas.analysis import NicheClusterAnalysisRead
from app.schemas.sachbuch import SachbuchAnalysisRead
from app.schemas.signal import OpportunitySignalRead
from app.services.scoring_engine import clamp


def build_cluster_signals(
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None = None,
) -> list[OpportunitySignalRead]:
    score = cluster_analysis.score
    summary = cluster_analysis.competitor_summary

    demand_strength = clamp(
        (score.demand_score or 0) * 0.72
        + summary.bsr_snapshot_coverage * 0.18
        + (score.new_entrant_signal or 0) * 0.10
    )
    market_openness = clamp(
        (score.entry_feasibility_score or 0) * 0.54
        + summary.new_entrant_visibility * 0.20
        + summary.low_review_visibility * 0.12
        + max(0, 100 - (score.brand_dominance_risk or 0)) * 0.14
    )
    review_access = clamp(
        max(0, 100 - (score.review_wall_risk or 0)) * 0.65
        + max(0, 100 - int(summary.average_review_count or 0)) * 0.15
        + summary.low_review_visibility * 0.20
    )
    gap_depth = clamp(
        (score.differentiation_score or 0) * 0.66
        + (score.review_insight_score or 0) * 0.34
    )
    risk_burden = max(
        score.compliance_risk or 0,
        score.authority_risk or 0,
        score.content_complexity_risk or 0,
    )

    signals = [
        _signal(
            key="demand_strength",
            label="Demand Strength",
            category="demand",
            direction="positive",
            score=demand_strength,
            summary=(
                f"{cluster_analysis.book_count} visible books and {cluster_analysis.keyword_count} related keywords "
                f"show recurring demand, with {summary.bsr_snapshot_coverage}% BSR coverage."
            ),
            evidence=[
                f"Demand score {score.demand_score or 0}/100",
                f"New entrant signal {score.new_entrant_signal or 0}/100",
                f"BSR coverage {summary.bsr_snapshot_coverage}%",
            ],
        ),
        _signal(
            key="market_openness",
            label="Market Openness",
            category="competition",
            direction="positive" if market_openness >= 50 else "negative",
            score=market_openness,
            summary=(
                "Visible rankings still leave room for a new book."
                if market_openness >= 50
                else "Top competitors still look relatively entrenched."
            ),
            evidence=[
                f"Entry feasibility {score.entry_feasibility_score or 0}/100",
                f"New entrant visibility {summary.new_entrant_visibility}/100",
                f"Publisher concentration {summary.publisher_concentration}/100",
            ],
        ),
        _signal(
            key="review_access",
            label="Review Access",
            category="competition",
            direction="positive" if review_access >= 50 else "negative",
            score=review_access,
            summary=(
                "Review counts do not fully lock the market."
                if review_access >= 50
                else "Review density still creates a heavy entry barrier."
            ),
            evidence=[
                f"Review wall risk {score.review_wall_risk or 0}/100",
                f"Average visible reviews {round(summary.average_review_count, 1)}",
                f"Low-review visibility {summary.low_review_visibility}/100",
            ],
        ),
        _signal(
            key="gap_depth",
            label="Differentiation Gap",
            category="gap",
            direction="positive" if gap_depth >= 50 else "negative",
            score=gap_depth,
            summary=(
                "Competitor weaknesses and review complaints point to a clear product gap."
                if gap_depth >= 50
                else "The visible gap still looks thin or generic."
            ),
            evidence=_top_items(
                [
                    f"Differentiation score {score.differentiation_score or 0}/100",
                    f"Review insight score {score.review_insight_score or 0}/100",
                    *cluster_analysis.top_opportunities[:2],
                    *cluster_analysis.missing_features[:2],
                ]
            ),
        ),
        _signal(
            key="risk_burden",
            label="Risk Burden",
            category="risk",
            direction="negative" if risk_burden >= 45 else "positive",
            score=risk_burden,
            summary=(
                "Authority, compliance, or complexity risks stay material."
                if risk_burden >= 45
                else "Risk stays comparatively manageable."
            ),
            evidence=[
                f"Compliance risk {score.compliance_risk or 0}/100",
                f"Authority risk {score.authority_risk or 0}/100",
                f"Content complexity {score.content_complexity_risk or 0}/100",
            ],
        ),
    ]

    if (score.ai_slop_score or 0) >= 50 and (score.demand_score or 0) >= 45:
        signals.append(
            _signal(
                key="ai_slop_opportunity",
                label="AI-Slop Opportunity",
                category="gap",
                direction="positive",
                score=score.ai_slop_score or 0,
                summary="Demand exists, but parts of the market still look generic, repetitive, or weakly localized.",
                evidence=_top_items(
                    [
                        f"AI-slop score {score.ai_slop_score or 0}/100",
                        *cluster_analysis.top_complaints[:2],
                        *cluster_analysis.top_opportunities[:1],
                    ]
                ),
            )
        )

    if sachbuch_analysis is not None:
        signals.extend(_build_sachbuch_extensions(sachbuch_analysis))

    return signals[:8]


def build_sachbuch_signals(
    sachbuch_analysis: SachbuchAnalysisRead,
) -> list[OpportunitySignalRead]:
    score = sachbuch_analysis.sachbuch_score
    topic_gap = sachbuch_analysis.topic_gap
    return [
        _signal(
            key="german_demand_signal",
            label="German Demand",
            category="demand",
            direction="positive",
            score=score.german_demand_signal or 0,
            summary="German-language demand signals are strong enough to justify deeper sachbuch work.",
            evidence=[
                f"Generic opportunity score {sachbuch_analysis.opportunity_score or 0}/100",
                f"Sachbuch score {score.final_score or 0}/100",
                f"German demand signal {score.german_demand_signal or 0}/100",
            ],
        ),
        _signal(
            key="topic_gap_signal",
            label="Topic Gap",
            category="gap",
            direction="positive" if (score.topic_gap_signal or 0) >= 50 else "negative",
            score=score.topic_gap_signal or 0,
            summary=(
                "Listings and reviews expose structural holes in the current sachbuch market."
                if (score.topic_gap_signal or 0) >= 50
                else "The topic gap is still not very pronounced."
            ),
            evidence=_top_items(
                [
                    f"Topic gap signal {score.topic_gap_signal or 0}/100",
                    f"Missing examples {topic_gap.missing_examples_signal or 0}/100",
                    f"Missing checklists {topic_gap.missing_checklists_signal or 0}/100",
                    topic_gap.topic_gap_summary,
                ]
            ),
        ),
        _signal(
            key="localization_gap",
            label="Localization Gap",
            category="gap",
            direction="positive" if (topic_gap.localization_gap_signal or 0) >= 40 else "negative",
            score=topic_gap.localization_gap_signal or 0,
            summary=(
                "German-specific localization looks under-served."
                if (topic_gap.localization_gap_signal or 0) >= 40
                else "Localization does not appear to be the main gap."
            ),
            evidence=[
                f"Localization gap {topic_gap.localization_gap_signal or 0}/100",
                *sachbuch_analysis.category_strategy[:2],
            ],
        ),
        _signal(
            key="research_burden",
            label="Research Burden",
            category="risk",
            direction="negative" if (score.research_effort_risk or 0) >= 45 else "positive",
            score=score.research_effort_risk or 0,
            summary=(
                "This sachbuch angle needs real source work and careful development."
                if (score.research_effort_risk or 0) >= 45
                else "Research burden looks manageable for this topic."
            ),
            evidence=_top_items(
                [
                    f"Research effort risk {score.research_effort_risk or 0}/100",
                    f"Authority risk {score.authority_risk or 0}/100",
                    *sachbuch_analysis.source_requirements[:2],
                ]
            ),
        ),
        _signal(
            key="liability_risk",
            label="Liability Risk",
            category="risk",
            direction="negative" if (score.liability_risk or 0) >= 45 else "positive",
            score=score.liability_risk or 0,
            summary=(
                "Legal, medical, or expert-review burdens remain material."
                if (score.liability_risk or 0) >= 45
                else "Liability burden stays comparatively contained."
            ),
            evidence=_top_items(
                [
                    f"Liability risk {score.liability_risk or 0}/100",
                    f"Update risk {score.update_risk or 0}/100",
                    *sachbuch_analysis.expert_needs[:2],
                ]
            ),
        ),
    ]


def build_candidate_signals(candidate: DiscoveryCandidate) -> list[OpportunitySignalRead]:
    positioning_specificity = clamp(
        (candidate.generation_score or 0) * 0.46
        + (candidate.specificity_score or 0) * 0.24
        + (candidate.audience_clarity_score or 0) * 0.15
        + (candidate.format_suitability_score or 0) * 0.15
    )
    raw_production_difficulty = (
        candidate.production_difficulty_score
        if candidate.production_difficulty_score is not None
        else candidate.production_effort_score
    )
    production_simplicity = max(0, 100 - (raw_production_difficulty or 0))

    signals = [
        _signal(
            key="positioning_specificity",
            label="Positioning Specificity",
            category="positioning",
            direction="positive" if positioning_specificity >= 50 else "negative",
            score=positioning_specificity,
            summary=(
                "Audience, use case, and format are specific enough to position clearly."
                if positioning_specificity >= 50
                else "The idea still needs sharper positioning."
            ),
            evidence=_top_items(
                [
                    f"Idea score {candidate.generation_score or 0}/100",
                    f"Specificity {candidate.specificity_score or 0}/100",
                    f"Audience clarity {candidate.audience_clarity_score or 0}/100",
                    f"Format fit {candidate.format_suitability_score or 0}/100",
                ]
            ),
        ),
        _signal(
            key="candidate_production_simplicity",
            label="Production Simplicity",
            category="positioning",
            direction="positive" if production_simplicity >= 50 else "negative",
            score=production_simplicity,
            summary=(
                "This concept looks practical to produce without extreme depth or overhead."
                if production_simplicity >= 50
                else "Production burden remains relatively high."
            ),
            evidence=[
                f"Production difficulty {raw_production_difficulty or 0}/100",
                f"Book type {candidate.validated_book_type or candidate.book_type_hint or 'unclassified'}",
            ],
        ),
    ]

    is_validated = all(
        value is not None
        for value in [
            candidate.demand_score,
            candidate.competition_score,
            candidate.gap_score,
            candidate.risk_score,
        ]
    )
    if not is_validated:
        signals.append(
            _signal(
                key="validation_pending",
                label="Validation Pending",
                category="demand",
                direction="neutral",
                score=candidate.generation_score or 0,
                summary="Idea-generation signals exist, but live Amazon market validation has not completed yet.",
                evidence=_top_items(
                    [
                        f"Status {candidate.status}",
                        f"Idea score {candidate.generation_score or 0}/100",
                        candidate.validation_notes,
                    ]
                ),
            )
        )
        return signals

    signals.extend(
        [
        _signal(
            key="candidate_demand_strength",
            label="Demand Strength",
            category="demand",
            direction="positive" if (candidate.demand_score or 0) >= 50 else "negative",
            score=candidate.demand_score or 0,
            summary=(
                "The validated market still shows enough demand to justify deeper work."
                if (candidate.demand_score or 0) >= 50
                else "Validated demand is still weak or shallow."
            ),
            evidence=_top_items(
                [
                    f"Relevant books {candidate.relevant_book_count or 0}",
                    f"Related keywords {candidate.related_keyword_count or 0}",
                    f"BSR coverage {candidate.bsr_coverage or 0}%",
                    candidate.market_summary,
                ]
            ),
        ),
        _signal(
            key="candidate_market_openness",
            label="Market Openness",
            category="competition",
            direction="positive" if (candidate.competition_score or 0) >= 50 else "negative",
            score=candidate.competition_score or 0,
            summary=(
                "The market still looks beatable for a cleaner offer."
                if (candidate.competition_score or 0) >= 50
                else "Competitor strength still looks heavy."
            ),
            evidence=_top_items(
                [
                    f"Competition score {candidate.competition_score or 0}/100",
                    f"Median visible reviews {candidate.top_competitor_review_median or 0}",
                    candidate.reason_summary,
                ]
            ),
        ),
        _signal(
            key="candidate_gap_strength",
            label="Product Gap",
            category="gap",
            direction="positive" if (candidate.gap_score or 0) >= 50 else "negative",
            score=candidate.gap_score or 0,
            summary=(
                "The market gap is strong enough to suggest a concrete angle."
                if (candidate.gap_score or 0) >= 50
                else "The product gap still needs clearer proof."
            ),
            evidence=_top_items(
                [
                    f"Gap score {candidate.gap_score or 0}/100",
                    candidate.gap_summary,
                    candidate.recommended_angle,
                ]
            ),
        ),
        _signal(
            key="candidate_risk_burden",
            label="Risk Burden",
            category="risk",
            direction="negative" if (candidate.risk_score or 0) >= 45 else "positive",
            score=candidate.risk_score or 0,
            summary=(
                "Compliance, authority, or complexity risks still matter."
                if (candidate.risk_score or 0) >= 45
                else "Risk stays comparatively manageable."
            ),
            evidence=_top_items(
                [
                    f"Risk score {candidate.risk_score or 0}/100",
                    candidate.validation_notes,
                ]
            ),
        ),
        ]
    )
    return signals


def _build_sachbuch_extensions(
    sachbuch_analysis: SachbuchAnalysisRead,
) -> list[OpportunitySignalRead]:
    topic_gap = sachbuch_analysis.topic_gap
    score = sachbuch_analysis.sachbuch_score
    return [
        _signal(
            key="localization_gap",
            label="Localization Gap",
            category="gap",
            direction="positive" if (topic_gap.localization_gap_signal or 0) >= 40 else "negative",
            score=topic_gap.localization_gap_signal or 0,
            summary=(
                "German-specific localization looks under-served."
                if (topic_gap.localization_gap_signal or 0) >= 40
                else "Localization is not the dominant gap."
            ),
            evidence=[
                f"Localization gap {topic_gap.localization_gap_signal or 0}/100",
                *sachbuch_analysis.positioning_angles[:1],
            ],
        ),
        _signal(
            key="freshness_need",
            label="Freshness Need",
            category="gap",
            direction="positive" if (score.freshness_need_signal or 0) >= 40 else "negative",
            score=score.freshness_need_signal or 0,
            summary=(
                "The topic shows room for a more current, updated treatment."
                if (score.freshness_need_signal or 0) >= 40
                else "Freshness does not appear to be the main gap."
            ),
            evidence=[
                f"Freshness need {score.freshness_need_signal or 0}/100",
                f"Outdated content {topic_gap.outdated_content_signal or 0}/100",
            ],
        ),
        _signal(
            key="research_burden",
            label="Research Burden",
            category="risk",
            direction="negative" if (score.research_effort_risk or 0) >= 45 else "positive",
            score=score.research_effort_risk or 0,
            summary=(
                "This topic needs heavier source work and subject-matter care."
                if (score.research_effort_risk or 0) >= 45
                else "Research burden looks manageable."
            ),
            evidence=[
                f"Research effort risk {score.research_effort_risk or 0}/100",
                f"Liability risk {score.liability_risk or 0}/100",
            ],
        ),
    ]


def _signal(
    *,
    key: str,
    label: str,
    category: str,
    direction: str,
    score: int,
    summary: str,
    evidence: list[str],
) -> OpportunitySignalRead:
    return OpportunitySignalRead(
        key=key,
        label=label,
        category=category,
        direction=direction,
        score=clamp(score),
        summary=summary,
        evidence=_top_items(evidence),
    )


def _top_items(values: list[str | None], *, limit: int = 4) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = (value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        items.append(normalized)
        if len(items) >= limit:
            break
    return items
