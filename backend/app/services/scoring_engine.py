from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median

from app.models.review import ReviewCluster


SENSITIVE_TERM_WEIGHTS = {
    "medizin": 35,
    "gesundheit": 30,
    "blutdruck": 28,
    "diabetes": 32,
    "therapie": 34,
    "recht": 36,
    "steuer": 36,
    "finanz": 34,
    "investment": 36,
    "pflege": 24,
    "depression": 35,
    "adhs": 28,
    "angst": 28,
    "prüfung": 18,
}

SPECIFICITY_MODIFIERS = [
    "für",
    "mit",
    "ohne",
    "praxis",
    "checkliste",
    "vorlage",
    "tracker",
    "tagebuch",
    "senior",
    "anfänger",
    "alltag",
    "deutschland",
]

AI_SLOP_TERMS = [
    "generisch",
    "oberflächlich",
    "wiederholung",
    "übersetzung",
    "ki",
    "allgemein",
    "lieblos",
]

COMPLIANCE_TERMS = {
    "medizin": 68,
    "gesundheit": 62,
    "therapie": 72,
    "recht": 78,
    "steuer": 80,
    "finanz": 74,
    "investment": 82,
    "copyright": 58,
    "urheberrecht": 64,
    "marke": 54,
    "trademark": 58,
}


@dataclass(frozen=True)
class OpportunityScorecard:
    keyword_specificity_score: int
    new_entrant_signal: int
    review_insight_score: int
    demand_score: int
    saturation_risk: int
    entry_feasibility_score: int
    review_wall_risk: int
    differentiation_score: int
    ai_slop_score: int
    brand_dominance_risk: int
    content_complexity_risk: int
    compliance_risk: int
    price_compression_risk: int
    authority_risk: int
    research_effort_score: int
    final_score: int
    explanation: str


def compute_opportunity_scorecard(
    *,
    keyword_text: str,
    book_type: str | None,
    related_keyword_count: int,
    visible_result_count: int,
    top_review_counts: list[int],
    top_ratings: list[float],
    top_prices: list[float],
    top_positions: list[int],
    top_titles: list[str],
    top_publishers: list[str],
    review_clusters: list[ReviewCluster],
    bsr_histories: list[list[int]],
) -> OpportunityScorecard:
    keyword_specificity_score = compute_keyword_specificity_score(keyword_text)
    new_entrant_signal = _new_entrant_signal(top_review_counts, top_positions)
    review_insight_score = _review_insight_score(review_clusters)
    brand_dominance_risk = _brand_dominance_risk(top_publishers)
    title_similarity = _title_similarity_score(top_titles)
    bsr_market_score = _bsr_market_score(bsr_histories)
    review_wall_risk = _review_wall_risk(top_review_counts)
    price_compression_risk = _price_compression_risk(top_prices)
    ai_slop_score = _ai_slop_score(top_titles, top_publishers, review_clusters, title_similarity)
    content_complexity_risk = keyword_complexity_risk(keyword_text)
    compliance_risk = _compliance_risk(keyword_text, review_clusters)
    authority_risk = _authority_risk(keyword_text, book_type)
    research_effort_score = _research_effort_score(book_type, authority_risk, content_complexity_risk)

    avg_rating = mean(top_ratings) if top_ratings else 0.0
    avg_review_count = mean(top_review_counts) if top_review_counts else 0.0
    avg_rating_text = f"{avg_rating:.2f}" if top_ratings else "0.00"
    books_with_reviews = sum(1 for count in top_review_counts if count > 0)
    low_review_visible = sum(1 for count in top_review_counts if 0 < count <= 100)
    strong_competitors = sum(1 for count in top_review_counts if count >= 300)

    demand_score = clamp(
        round(
            8
            + min(18, related_keyword_count * 3)
            + min(14, visible_result_count * 0.7)
            + min(24, books_with_reviews * 2.5)
            + bsr_market_score * 0.30
            + new_entrant_signal * 0.12
            + (18 if avg_review_count >= 80 else avg_review_count / 5)
        )
    )
    saturation_risk = clamp(
        round(
            review_wall_risk * 0.28
            + brand_dominance_risk * 0.24
            + title_similarity * 0.18
            + price_compression_risk * 0.14
            + strong_competitors * 4
            + max(0, (avg_rating - 4.5) * 40)
        )
    )
    entry_feasibility_score = clamp(
        round(
            18
            + keyword_specificity_score * 0.28
            + new_entrant_signal * 0.34
            + low_review_visible * 4
            + max(0, 55 - brand_dominance_risk) * 0.12
            - review_wall_risk * 0.16
            - strong_competitors * 4
        )
    )
    differentiation_score = clamp(
        round(
            12
            + review_insight_score * 0.42
            + ai_slop_score * 0.24
            + max(0, (4.75 - avg_rating) * 30)
            + title_similarity * 0.10
            + max(0, 100 - brand_dominance_risk) * 0.08
        )
    )

    final_score = clamp(
        round(
            demand_score * 0.24
            + entry_feasibility_score * 0.20
            + keyword_specificity_score * 0.10
            + differentiation_score * 0.14
            + new_entrant_signal * 0.10
            + review_insight_score * 0.08
            + ai_slop_score * 0.06
            - saturation_risk * 0.18
            - review_wall_risk * 0.12
            - brand_dominance_risk * 0.06
            - content_complexity_risk * 0.06
            - compliance_risk * 0.05
            - authority_risk * 0.04
            - price_compression_risk * 0.04
            + 10
        )
    )

    explanation = (
        f"Specificity {keyword_specificity_score}, new-entrant signal {new_entrant_signal}, "
        f"review insight {review_insight_score}, BSR market score {bsr_market_score}, "
        f"brand dominance risk {brand_dominance_risk}, review wall risk {review_wall_risk}, "
        f"title similarity {title_similarity}, price compression {price_compression_risk}, "
        f"content complexity {content_complexity_risk}, compliance risk {compliance_risk}, "
        f"authority risk {authority_risk}, avg review count {avg_review_count:.1f}, "
        f"and avg rating {avg_rating_text} informed the final score."
    )

    return OpportunityScorecard(
        keyword_specificity_score=keyword_specificity_score,
        new_entrant_signal=new_entrant_signal,
        review_insight_score=review_insight_score,
        demand_score=demand_score,
        saturation_risk=saturation_risk,
        entry_feasibility_score=entry_feasibility_score,
        review_wall_risk=review_wall_risk,
        differentiation_score=differentiation_score,
        ai_slop_score=ai_slop_score,
        brand_dominance_risk=brand_dominance_risk,
        content_complexity_risk=content_complexity_risk,
        compliance_risk=compliance_risk,
        price_compression_risk=price_compression_risk,
        authority_risk=authority_risk,
        research_effort_score=research_effort_score,
        final_score=final_score,
        explanation=explanation,
    )


def compute_keyword_specificity_score(keyword: str) -> int:
    lowered = keyword.casefold()
    tokens = [token for token in lowered.replace("-", " ").split() if token]
    score = 12

    if len(tokens) >= 3:
        score += 28
    elif len(tokens) == 2:
        score += 20
    elif len(keyword) >= 14:
        score += 18
    else:
        score += 10

    modifier_hits = sum(1 for modifier in SPECIFICITY_MODIFIERS if modifier in lowered)
    score += min(28, modifier_hits * 8)

    if any(char.isdigit() for char in keyword):
        score += 6
    if len(keyword) >= 20:
        score += 6
    if lowered in {"ratgeber", "tagebuch", "buch", "handbuch", "ki"}:
        score -= 18

    return clamp(score)


def keyword_complexity_risk(keyword: str) -> int:
    lowered = keyword.casefold()
    risk = 10
    for term, weight in SENSITIVE_TERM_WEIGHTS.items():
        if term in lowered:
            risk = max(risk, weight)
    if "heil" in lowered or "garantie" in lowered:
        risk = max(risk, 40)
    return clamp(risk)


def clamp(value: int | float) -> int:
    return max(0, min(100, int(round(value))))


def _new_entrant_signal(top_review_counts: list[int], top_positions: list[int]) -> int:
    if not top_review_counts:
        return 0
    signal = 0.0
    for index, review_count in enumerate(top_review_counts[:10]):
        position = top_positions[index] if index < len(top_positions) else index + 1
        if 0 < review_count <= 30:
            signal += max(4, 14 - position)
        elif 31 <= review_count <= 100:
            signal += max(2, 8 - position * 0.4)
    return clamp(signal * 3)


def _review_insight_score(review_clusters: list[ReviewCluster]) -> int:
    if not review_clusters:
        return 0
    frequencies = [cluster.frequency or 1 for cluster in review_clusters]
    severities = [cluster.severity or 1 for cluster in review_clusters]
    negative_clusters = sum(1 for cluster in review_clusters if cluster.sentiment != "positive")
    cluster_names = {cluster.cluster_name.strip().casefold() for cluster in review_clusters if cluster.cluster_name}
    return clamp(
        10
        + min(30, len(cluster_names) * 3)
        + min(25, mean(frequencies) * 2)
        + min(20, mean(severities) * 4)
        + negative_clusters * 3
    )


def _brand_dominance_risk(top_publishers: list[str]) -> int:
    normalized = [(publisher or "unknown").strip().casefold() for publisher in top_publishers if publisher]
    if not normalized:
        return 0
    counts: dict[str, int] = {}
    for publisher in normalized:
        counts[publisher] = counts.get(publisher, 0) + 1
    max_share = max(counts.values()) / len(normalized)
    unique_penalty = max(0, 4 - len(counts)) * 6
    return clamp(max_share * 70 + unique_penalty)


def _title_similarity_score(top_titles: list[str]) -> int:
    tokensets: list[set[str]] = []
    for title in top_titles:
        tokens = {token for token in title.casefold().replace(":", " ").replace("–", " ").split() if len(token) > 3}
        if tokens:
            tokensets.append(tokens)
    if len(tokensets) < 2:
        return 0
    scores: list[float] = []
    for index, tokens in enumerate(tokensets):
        for compare in tokensets[index + 1:]:
            union = len(tokens | compare)
            if union == 0:
                continue
            scores.append((len(tokens & compare) / union) * 100)
    return clamp(mean(scores)) if scores else 0


def _price_compression_risk(top_prices: list[float]) -> int:
    if len(top_prices) < 3:
        return 20
    max_price = max(top_prices)
    min_price = min(top_prices)
    if max_price <= 0:
        return 20
    spread_ratio = (max_price - min_price) / max_price
    median_price = median(top_prices)
    compression = 100 - clamp(spread_ratio * 100)
    cheap_market_bonus = 10 if median_price < 8 else 0
    return clamp(compression * 0.7 + cheap_market_bonus)


def _bsr_market_score(bsr_histories: list[list[int]]) -> int:
    valid_histories = [history for history in bsr_histories if history]
    if not valid_histories:
        return 0

    latest_values = [history[-1] for history in valid_histories]
    avg_latest = mean(latest_values)
    avg_latest_component = max(0.0, 55 - min(55.0, avg_latest / 25000))

    stability_scores: list[float] = []
    improvement_scores = 0.0
    for history in valid_histories:
        max_value = max(history)
        min_value = min(history)
        volatility = ((max_value - min_value) / max_value) * 100 if max_value else 0.0
        stability_scores.append(max(0.0, 100 - volatility))
        if history[-1] <= history[0]:
            improvement_scores += 12

    coverage_component = (len(valid_histories) / max(1, len(bsr_histories))) * 25
    stability_component = mean(stability_scores) * 0.28 if stability_scores else 0.0
    return clamp(avg_latest_component + coverage_component + stability_component + improvement_scores)


def _review_wall_risk(top_review_counts: list[int]) -> int:
    if not top_review_counts:
        return 0
    median_reviews = median(top_review_counts)
    top3 = max(top_review_counts[:3], default=0)
    distribution_penalty = mean(sorted(top_review_counts, reverse=True)[:5]) if len(top_review_counts) >= 5 else mean(top_review_counts)
    return clamp(median_reviews / 5 + top3 / 18 + distribution_penalty / 20)


def _ai_slop_score(
    top_titles: list[str],
    top_publishers: list[str],
    review_clusters: list[ReviewCluster],
    title_similarity: int,
) -> int:
    colon_titles = sum(1 for title in top_titles if ":" in title or "–" in title)
    repeated_publishers = len(top_publishers) - len({publisher.casefold() for publisher in top_publishers if publisher})
    review_text = " ".join(
        part
        for cluster in review_clusters
        for part in [cluster.cluster_name, cluster.summary, cluster.example_snippets]
        if part
    ).casefold()
    review_hits = sum(1 for term in AI_SLOP_TERMS if term in review_text)
    return clamp(colon_titles * 6 + repeated_publishers * 10 + title_similarity * 0.35 + review_hits * 8)


def _authority_risk(keyword_text: str, book_type: str | None) -> int:
    base = 20 if book_type == "sachbuch" else 8
    return clamp(max(base, keyword_complexity_risk(keyword_text) + (8 if book_type == "sachbuch" else 0)))


def _compliance_risk(keyword_text: str, review_clusters: list[ReviewCluster]) -> int:
    lowered = keyword_text.casefold()
    review_text = " ".join(
        part
        for cluster in review_clusters
        for part in [cluster.cluster_name, cluster.summary, cluster.example_snippets]
        if part
    ).casefold()
    base = max(10, _score_terms(lowered, COMPLIANCE_TERMS))
    if "heil" in lowered or "garantie" in lowered:
        base = max(base, 70)
    if any(term in review_text for term in ["falsch", "ungenau", "gefährlich", "haftung"]):
        base += 8
    return clamp(base)


def _research_effort_score(book_type: str | None, authority_risk: int, content_complexity_risk: int) -> int:
    base = 38 if book_type == "sachbuch" else 18
    return clamp(base + authority_risk * 0.45 + content_complexity_risk * 0.25)


def _score_terms(text: str, weights: dict[str, int]) -> int:
    score = 0
    for term, weight in weights.items():
        if term in text:
            score += weight
    return clamp(score)
