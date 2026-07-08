"""
Semantic Compatibility Engine — checks if topic + audience actually belong together.

Uses domain compatibility maps, incompatible pairs, and graph relation checks
to determine if a candidate combination makes semantic sense.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.discovery.domain_compatibility_rules import (
    DOMAIN_AUDIENCE_COMPATIBILITY,
    INCOMPATIBLE_COMBINATIONS,
)


@dataclass(frozen=True)
class CompatibilityResult:
    compatible: bool
    score: int  # 0-100
    reason: str
    hard_block: bool
    suggested_rewrite: str | None


def check_semantic_compatibility(
    topic: str | None,
    audience: str | None,
    problem: str | None = None,
    book_format: str | None = None,
) -> CompatibilityResult:
    """Check if topic and audience are a semantically valid KDP niche combination.

    Returns CompatibilityResult with score and block/allow decision.
    """
    if not topic or not audience:
        return CompatibilityResult(
            compatible=False,
            score=0,
            reason="Missing topic or audience",
            hard_block=False,
            suggested_rewrite=None,
        )

    topic_key = topic.casefold().strip()
    audience_key = audience.casefold().strip()

    # ── Check explicit incompatible pairs ──────────────────────────
    pair = (topic_key, audience_key)
    if pair in INCOMPATIBLE_COMBINATIONS:
        # Try to find a compatible audience
        compat_audiences = DOMAIN_AUDIENCE_COMPATIBILITY.get(topic_key, [])
        suggestion = None
        if compat_audiences:
            suggestion = f"{topic} für {compat_audiences[0]}"

        return CompatibilityResult(
            compatible=False,
            score=20,
            reason=f"'{topic}' and '{audience}' are an incompatible combination for KDP",
            hard_block=True,
            suggested_rewrite=suggestion,
        )

    # ── Check explicit compatible pairs ────────────────────────────
    compat_audiences = DOMAIN_AUDIENCE_COMPATIBILITY.get(topic_key, [])
    if compat_audiences and audience_key in compat_audiences:
        return CompatibilityResult(
            compatible=True,
            score=90,
            reason=f"Topic '{topic}' and audience '{audience}' are a known compatible KDP pair",
            hard_block=False,
            suggested_rewrite=None,
        )

    # ── Check partial match: topic words in audience compatibility ──
    topic_words = topic_key.split()
    for word in topic_words:
        if len(word) < 3:
            continue
        partial_compat = DOMAIN_AUDIENCE_COMPATIBILITY.get(word, [])
        if audience_key in partial_compat:
            return CompatibilityResult(
                compatible=True,
                score=75,
                reason=f"Partial match: '{word}' is compatible with '{audience}'",
                hard_block=False,
                suggested_rewrite=None,
            )

    # ── Check reverse: audience as topic ───────────────────────────
    if audience_key in DOMAIN_AUDIENCE_COMPATIBILITY:
        aud_compat = DOMAIN_AUDIENCE_COMPATIBILITY[audience_key]
        if any(tw in aud_compat for tw in topic_words):
            return CompatibilityResult(
                compatible=True,
                score=65,
                reason=f"Reverse compatibility: '{audience}' audience has '{topic}' in domain",
                hard_block=False,
                suggested_rewrite=None,
            )

    # ── Check if topic IS actually an audience ─────────────────────
    audience_names = {"pflege", "eltern", "senioren", "selbstständige",
                      "rentner", "ruheständler", "anfänger", "freelancer",
                      "handwerker", "schüler", "studenten", "alleinerziehende",
                      "kleinunternehmer", "gründer"}
    if topic_key in audience_names:
        suggestion = None
        if audience_key in DOMAIN_AUDIENCE_COMPATIBILITY:
            suggestion = None
        return CompatibilityResult(
            compatible=False,
            score=15,
            reason=f"'{topic}' is an audience, not a topic — cannot be used as main topic",
            hard_block=True,
            suggested_rewrite=f"Alltag organisieren für {topic}" if topic_key == "eltern" else None,
        )

    # ── Generic: no domain rule found, allow but with low confidence ─
    return CompatibilityResult(
        compatible=True,
        score=50,
        reason=f"No domain rules found for '{topic}' + '{audience}' — allowed but unverified",
        hard_block=False,
        suggested_rewrite=None,
    )


def get_rewrite_suggestions(
    topic: str | None,
    audience: str | None,
) -> list[str]:
    """Generate alternative candidate rewrites for bad combinations."""
    if not topic or not audience:
        return []

    topic_key = topic.casefold().strip()
    suggestions: list[str] = []

    # If topic has known compatible audiences, suggest those
    compat_audiences = DOMAIN_AUDIENCE_COMPATIBILITY.get(topic_key, [])
    for aud in compat_audiences[:3]:
        if aud != audience.casefold():
            suggestions.append(f"{topic} für {aud}")

    # If audience has known compatible topics, suggest those
    audience_key = audience.casefold().strip()
    for t_key, aud_list in DOMAIN_AUDIENCE_COMPATIBILITY.items():
        if audience_key in aud_list and t_key != topic_key:
            suggestions.append(f"{t_key} für {audience}")
            if len(suggestions) >= 5:
                break

    return suggestions[:5]
