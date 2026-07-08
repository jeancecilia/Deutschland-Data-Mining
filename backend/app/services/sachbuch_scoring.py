from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import mean

from app.models.book import Book
from app.models.report import SachbuchTopicGap
from app.models.review import ReviewCluster
from app.services.market_intelligence import category_labels_for_book
from app.services.scoring_engine import clamp, keyword_complexity_risk


LIABILITY_TERMS = {
    "medizin": 70,
    "gesund": 65,
    "therapie": 72,
    "recht": 78,
    "steuer": 78,
    "finanz": 72,
    "investment": 84,
    "blutdruck": 68,
}

UPDATE_TERMS = {
    "ki": 18,
    "chatgpt": 22,
    "gesetz": 24,
    "steuer": 24,
    "recht": 24,
    "datenschutz": 20,
}

EVERGREEN_TERMS = {
    "organisation": 18,
    "alltag": 18,
    "lernen": 18,
    "praxis": 14,
    "handwerker": 14,
}

MONETIZATION_TERMS = {
    "selbstständ": 18,
    "betrieb": 18,
    "kunden": 14,
    "umsatz": 18,
    "angebot": 14,
    "produktiv": 14,
}


@dataclass(frozen=True)
class SachbuchScorecard:
    german_demand_signal: int
    topic_gap_signal: int
    depth_weakness_signal: int
    freshness_need_signal: int
    localization_signal: int
    differentiation_signal: int
    evergreen_potential_signal: int
    monetization_potential_signal: int
    authority_risk: int
    research_effort_risk: int
    liability_risk: int
    update_risk: int
    publisher_dominance_risk: int
    review_wall_risk: int
    final_score: int
    explanation: str
    quality_warnings: list[str]


def compute_sachbuch_scorecard(
    *,
    keyword_text: str,
    books: list[Book],
    review_clusters: list[ReviewCluster],
    topic_gap: SachbuchTopicGap,
    generic_demand_score: int,
    generic_differentiation_score: int,
    generic_authority_risk: int,
    generic_research_effort_score: int,
    generic_review_wall_risk: int,
    publisher_dominance_risk: int,
) -> SachbuchScorecard:
    lowered_keyword = keyword_text.casefold()
    bsr_visible_books = sum(1 for book in books if any(category_labels_for_book(book)) or book.publication_date)
    page_counts = [book.page_count for book in books if book.page_count]
    avg_page_count = mean(page_counts) if page_counts else 0
    publication_ages = [
        max(0, date.today().year - book.publication_date.year)
        for book in books
        if book.publication_date
    ]
    avg_age = mean(publication_ages) if publication_ages else 0

    german_demand_signal = clamp(
        generic_demand_score * 0.55
        + min(24, len(books[:10]) * 2)
        + min(18, bsr_visible_books * 3)
    )
    topic_gap_signal = clamp(
        ((topic_gap.missing_examples_signal or 0) + (topic_gap.missing_checklists_signal or 0) + (topic_gap.localization_gap_signal or 0)) / 3
    )
    depth_weakness_signal = clamp(
        max(0, 100 - (topic_gap.content_depth_score or 0))
        + sum(
            6
            for cluster in review_clusters
            if any(
                term in " ".join(
                    part for part in [cluster.cluster_name, cluster.summary, cluster.example_snippets] if part
                ).casefold()
                for term in ["oberflächlich", "allgemein", "theoretisch", "beispiel", "praxis"]
            )
        )
    )
    freshness_need_signal = clamp((topic_gap.outdated_content_signal or 0) + min(18, avg_age * 4))
    localization_signal = clamp((topic_gap.localization_gap_signal or 0) + _score_terms(lowered_keyword, {"deutschland": 16, "deutsch": 10, "lokal": 10}))
    differentiation_signal = clamp(generic_differentiation_score * 0.6 + topic_gap_signal * 0.4)
    evergreen_potential_signal = clamp(40 + _score_terms(lowered_keyword, EVERGREEN_TERMS) - _score_terms(lowered_keyword, UPDATE_TERMS) * 0.35)
    monetization_potential_signal = clamp(35 + _score_terms(lowered_keyword, MONETIZATION_TERMS) + min(18, avg_page_count / 12))
    authority_risk = clamp(max(generic_authority_risk, keyword_complexity_risk(keyword_text) + 8))
    research_effort_risk = clamp(generic_research_effort_score + authority_risk * 0.2 + max(0, avg_page_count - 120) * 0.08)
    liability_risk = clamp(max(8, _score_terms(lowered_keyword, LIABILITY_TERMS)))
    update_risk = clamp(12 + _score_terms(lowered_keyword, UPDATE_TERMS) + (topic_gap.outdated_content_signal or 0) * 0.25)
    review_wall_risk = clamp(generic_review_wall_risk)

    final_score = clamp(
        german_demand_signal * 0.16
        + topic_gap_signal * 0.14
        + depth_weakness_signal * 0.10
        + freshness_need_signal * 0.08
        + localization_signal * 0.10
        + differentiation_signal * 0.12
        + evergreen_potential_signal * 0.08
        + monetization_potential_signal * 0.08
        - authority_risk * 0.07
        - research_effort_risk * 0.07
        - liability_risk * 0.08
        - update_risk * 0.05
        - publisher_dominance_risk * 0.04
        - review_wall_risk * 0.03
        + 12
    )

    quality_warnings: list[str] = []
    if liability_risk >= 60:
        quality_warnings.append("Haftungs- oder Beratungsrisiko ist erhöht; Aussagen nur mit sauberem Disclaimer und Quellenbezug.")
    if authority_risk >= 55:
        quality_warnings.append("Fachprüfung oder belastbare Primärquellen sollten vor Veröffentlichung eingeplant werden.")
    if update_risk >= 40:
        quality_warnings.append("Das Thema hat erhöhten Aktualisierungsdruck; Editionen und Update-Prozess mitdenken.")
    if publisher_dominance_risk >= 55:
        quality_warnings.append("Starke Verlags- oder Markenballung erschwert die Positionierung gegen etablierte Titel.")

    explanation = (
        f"Sachbuch score built from demand {german_demand_signal}, topic gap {topic_gap_signal}, "
        f"depth weakness {depth_weakness_signal}, freshness need {freshness_need_signal}, "
        f"localization {localization_signal}, evergreen {evergreen_potential_signal}, "
        f"monetization {monetization_potential_signal}, authority risk {authority_risk}, "
        f"liability risk {liability_risk}, update risk {update_risk}, and publisher dominance {publisher_dominance_risk}."
    )

    return SachbuchScorecard(
        german_demand_signal=german_demand_signal,
        topic_gap_signal=topic_gap_signal,
        depth_weakness_signal=depth_weakness_signal,
        freshness_need_signal=freshness_need_signal,
        localization_signal=localization_signal,
        differentiation_signal=differentiation_signal,
        evergreen_potential_signal=evergreen_potential_signal,
        monetization_potential_signal=monetization_potential_signal,
        authority_risk=authority_risk,
        research_effort_risk=research_effort_risk,
        liability_risk=liability_risk,
        update_risk=update_risk,
        publisher_dominance_risk=publisher_dominance_risk,
        review_wall_risk=review_wall_risk,
        final_score=final_score,
        explanation=explanation,
        quality_warnings=quality_warnings,
    )


def _score_terms(text: str, weights: dict[str, int]) -> int:
    score = 0
    for term, weight in weights.items():
        if term in text:
            score += weight
    return clamp(score)
