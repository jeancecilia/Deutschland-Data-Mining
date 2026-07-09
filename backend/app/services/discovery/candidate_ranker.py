"""
Candidate Ranker — scores candidates for validation priority.

Calibrated to reject generic template artifacts and reward concrete KDP concepts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from collections import Counter

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.discovery.entity_normalizer import normalize_entity_name
from app.services.discovery.format_fit_rules import score_format_fit

HIGH_INTENT_WORDS = {
    "tagebuch", "arbeitsbuch", "workbook", "planer", "checkliste",
    "ratgeber", "leitfaden", "journal", "tracker", "vorlagen",
    "trainingsjournal", "logbuch", "praxisbuch", "notizbuch",
}

GENERIC_FILLER = {"dinge", "sachen", "zeug", "kram", "thema", "bereich"}

GENERIC_TOPIC_WORDS = {
    "organisation", "beratung", "hilfe", "training", "optimierung",
    "planung", "grundlagen", "fortgeschritten", "dokumentation", "pflege",
}

CONCRETE_USE_CASE_WORDS = {
    "blutdruckwerte", "pflegegrad", "antrag", "rückruftraining",
    "hundebegegnungen", "steuerunterlagen", "belege", "rechnungen",
    "umzugscheckliste", "haushaltsbudget", "smartphone", "excel",
    "lebenslauf", "vorstellungsgespräch", "medikamentenplan",
    "blutdruck", "blutzucker", "diabetes", "demenz", "adhs",
    "buchhaltung", "steuererklärung", "bewerbung", "kündigung",
    "mietvertrag", "arbeitsvertrag", "rechnung", "fotografie",
    "programmieren", "kochen", "backen", "garten", "fitness",
    "yoga", "meditation", "sprache", "vokabeln", "grammatik",
    "führerschein", "prüfung", "abitur", "studium",
}

DOMAIN_AUDIENCE_COMPATIBILITY: dict[str, set[str]] = {
    "schule": {"eltern", "schueler", "lehrer", "azubis", "jugendliche"},
    "studium": {"studenten", "studierende", "anfaenger", "einsteiger"},
    "reise_umzug": {"familien", "paare", "singles", "senioren", "erwachsene"},
    "lokales_business": {"kleinunternehmer", "selbststaendige", "berufstaetige", "fachkraefte"},
    "it": {"anfaenger", "studenten", "azubis", "berufstaetige", "fachkraefte", "selbststaendige"},
    "business": {"selbststaendige", "kleinunternehmer", "fuehrungskraefte", "freelancer", "berufstaetige"},
    "pflege": {"pflegende_angehoerige", "senioren", "rentner", "erwachsene"},
    "gesundheit": {"senioren", "erwachsene", "jugendliche", "eltern"},
    "haustiere": {"tierhalter", "familien", "erwachsene", "senioren"},
    "kochen": {"anfaenger", "einsteiger", "familien", "erwachsene"},
    "fitness_sport": {"anfaenger", "einsteiger", "fortgeschrittene", "erwachsene", "jugendliche"},
    "finanzen": {"selbststaendige", "familien", "erwachsene", "rentner", "alleinerziehende"},
    "eltern_kind": {"eltern", "alleinerziehende", "familien"},
    "senioren": {"senioren", "rentner", "pflegende_angehoerige"},
    "lernen": {"schueler", "studenten", "erwachsene", "anfaenger", "einsteiger"},
}


@dataclass
class RankResult:
    ranked: int
    queued: int
    manual_review: int
    rejected_pre_validation: int
    top_score: int
    avg_score: float


def _score_naturalness(candidate_name: str) -> int:
    """Score how natural the phrase sounds. 0=awkward, 100=natural."""
    score = 100
    lowered = candidate_name.lower()
    words = lowered.split()

    word_counts = Counter(words)
    for w, c in word_counts.items():
        if c > 2 and w not in {"für", "und", "mit", "der", "die", "das", "den", "dem"}:
            score -= 15
            break

    fuer_count = lowered.count(" für ")
    if fuer_count > 2:
        score -= 20
    elif fuer_count > 1:
        score -= 10

    if len(words) > 12:
        score -= 15
    elif len(words) > 8:
        score -= 5

    for w, c in word_counts.items():
        if c > 2 and len(w) > 3:
            score -= 10
            break

    for filler in GENERIC_FILLER:
        if filler in words:
            score -= 10
            break

    # Phrase pattern penalty: "für AUDIENCE FORMAT" at end
    if re.search(r"für\s+\w+\s+(tagebuch|arbeitsbuch|leitfaden|trainingsjournal|ratgeber|planer|checkliste)$", lowered):
        score -= 20

    return max(0, score)


def _score_specificity(candidate_name: str, meta: dict | None) -> int:
    """Score 0–100 based on topic/audience/problem/format presence."""
    score = 0
    lowered = candidate_name.lower()

    if meta:
        if meta.get("macro_domain") or meta.get("micro_domain"):
            score += 15
        if meta.get("audience_hint"):
            if " für " in lowered:
                score += 20
            else:
                score += 10
        if meta.get("problem_hint"):
            score += 20
        if meta.get("format_hint"):
            score += 15

    if " für " in lowered:
        score = max(score, 50)  # raised from 40 — KDP title pattern indicator

    # Generic topic penalty
    generic_count = sum(1 for w in GENERIC_TOPIC_WORDS if w in lowered)
    if generic_count >= 2 and not any(cw in lowered for cw in CONCRETE_USE_CASE_WORDS):
        score -= 30
    elif generic_count >= 1 and not any(cw in lowered for cw in CONCRETE_USE_CASE_WORDS):
        score -= 20

    # Concrete use-case bonus
    if any(cw in lowered for cw in CONCRETE_USE_CASE_WORDS):
        score += 20
    elif score < 40:
        score -= 25  # no concrete use case at all

    return max(0, min(100, score))


def _score_intent(candidate_name: str, meta: dict | None) -> int:
    """Score 0–100 based on KDP buyer intent signals."""
    score = 0
    lowered = candidate_name.lower()
    for word in HIGH_INTENT_WORDS:
        if word in lowered:
            score += 15
    score = min(55, score)

    if " für " in lowered:
        score += 10
    if meta and meta.get("problem_hint"):
        score += 10
    # Strong KDP title pattern bonus
    if any(w in lowered for w in ["tagebuch", "checkliste", "ratgeber", "arbeitsbuch", "planer"]):
        if " für " in lowered:
            score += 15
    return min(100, score)


def _score_domain_fit(meta: dict | None) -> int:
    """Score 0–100 based on domain metadata presence."""
    if not meta:
        return 20
    score = 0
    if meta.get("macro_domain") or meta.get("domain"):
        score += 50  # raised from 30 — having any domain is valuable
    if meta.get("subdomain"):
        score += 25
    if meta.get("micro_domain"):
        score += 25
    return score


def _score_duplication(
    candidate_name: str, normalized: str,
    macro_domain: str | None,
    domain_candidates: dict[str, list[tuple[str, int]]],
) -> int:
    if not macro_domain:
        return 0
    siblings = domain_candidates.get(macro_domain, [])
    if not siblings:
        return 0
    name_words = set(candidate_name.lower().split())
    similar = 0
    for sib_name, _ in siblings:
        sib_words = set(sib_name.lower().split())
        overlap = len(name_words & sib_words) / max(len(name_words), 1)
        if overlap > 0.7:
            similar += 1
    if similar >= 3: return 80
    if similar >= 2: return 50
    if similar >= 1: return 20
    return 0


def _score_audience_fit(meta: dict | None) -> int:
    """Score how well the audience matches the macro domain. 0=mismatch, 100=perfect."""
    if not meta:
        return 50  # neutral
    macro = str(meta.get("macro_domain", meta.get("domain", ""))).lower()
    audience = str(meta.get("audience_hint", "")).lower()

    if not macro or not audience:
        return 50

    if macro in DOMAIN_AUDIENCE_COMPATIBILITY:
        compatible = DOMAIN_AUDIENCE_COMPATIBILITY[macro]
        if audience in compatible:
            return 90  # perfect match
        return 30  # weak match

    return 50  # unknown domain


def _score_format_style(candidate_name: str, meta: dict | None) -> int:
    """Penalize awkward format placements. 100=good, 0=bad."""
    score = 100
    lowered = candidate_name.lower()

    # "tagebuch" for business/help/advice domains without tracking context
    macro = str(meta.get("macro_domain", meta.get("domain", ""))).lower() if meta else ""
    has_tracking_context = any(w in lowered for w in {"blutdruck", "blutzucker", "training", "fitness", "lernen"})

    if "tagebuch" in lowered and macro in {"business", "admin_recht", "finanzen", "recht", "it"} and not has_tracking_context:
        score -= 30

    # "trainingsjournal" outside sports/dog/language/skills
    if "trainingsjournal" in lowered and not any(w in lowered for w in {"hund", "sport", "fitness", "training", "lernen", "musik", "sprache"}):
        score -= 30

    return max(0, score)


# German compound KDP patterns: concrete_object + format
COMPOUND_KDP_PATTERNS: dict[str, list[str]] = {
    "tagebuch": ["blutdruck", "blutzucker", "schmerz", "migräne", "symptom", "schlaf", "futter", "pflege"],
    "checkliste": ["pflegegrad", "umzug", "schulstart", "steuer", "bewerbung", "ecommerce"],
    "planer": ["medikamenten", "haushaltsbudget", "studium", "adhs", "garten", "content"],
    "arbeitsbuch": ["excel", "buchhaltung", "karriere", "lernen", "adhs"],
    "ratgeber": ["smartphone", "senioren", "pflege", "reise"],
    "vorlage": ["rechnung", "lebenslauf", "bewerbung", "businessplan"],
    "ordner": ["pflege", "notfall", "dokumente"],
}


def _score_compound_kdp_boost(candidate_name: str, source_entities: dict | None = None) -> int:
    """Score 0–12 for German compound KDP concepts. Checks candidate_name and canonical_micro_domain."""
    lowered = candidate_name.lower()
    # Also check canonical micro-domain from source_entities
    canonical = ""
    if source_entities:
        canonical = str(source_entities.get("canonical_micro_domain", "")).lower()
    check_texts = [lowered]
    if canonical and canonical != lowered:
        check_texts.append(canonical)

    for text in check_texts:
        for fmt_word, objects in COMPOUND_KDP_PATTERNS.items():
            if fmt_word in text:
                for obj in objects:
                    if obj in text and " für " in text:
                        return 12
        for fmt_word in COMPOUND_KDP_PATTERNS:
            if fmt_word in text and any(obj in text for obj in COMPOUND_KDP_PATTERNS[fmt_word]):
                return 6
    return 0


def _score_generic_pattern_penalty(candidate_name: str) -> int:
    """Score -20 for generic auto-fill patterns, 0 otherwise."""
    import re
    lowered = candidate_name.lower()
    if re.match(r"^[a-zäöüß]+ (hilfe|beratung|organisation|optimierung|planung|grundlagen|training) für ", lowered):
        # Check if it has a concrete object
        has_concrete = any(cw in lowered for cw in CONCRETE_USE_CASE_WORDS)
        if not has_concrete:
            return -20
    return 0


def rank_candidates_for_validation(
    db: Session,
    *,
    limit: int = 5000,
    min_score: int = 70,
    max_per_macro_domain: int = 100,
    max_per_subdomain: int = 30,
    max_per_micro_domain: int = 3,
) -> RankResult:
    from sqlalchemy import select as sa_select
    from app.models.discovery_pipeline import NicheCandidate

    candidates = list(db.scalars(
        sa_select(NicheCandidate).where(
            NicheCandidate.status.in_(["new", "needs_manual_review"])
        ).limit(limit)
    ))

    if not candidates:
        return RankResult(0, 0, 0, 0, 0, 0.0)

    domain_index: dict[str, list[tuple[str, int]]] = {}
    for c in candidates:
        se = c.source_entities or {}
        macro = se.get("macro_domain", se.get("domain", ""))
        if macro:
            domain_index.setdefault(str(macro), []).append((c.candidate_name, c.id))

    macro_counts: dict[str, int] = {}
    sub_counts: dict[str, int] = {}
    micro_counts: dict[str, int] = {}

    queued = 0
    manual_review = 0
    rejected = 0
    all_scores: list[int] = []
    top_score = 0

    for candidate in candidates:
        se = candidate.source_entities or {}
        macro = str(se.get("macro_domain", se.get("domain", "")))
        sub = str(se.get("subdomain", ""))
        micro = str(se.get("micro_domain", ""))
        name = candidate.candidate_name

        nat = _score_naturalness(name)
        spec = _score_specificity(name, se)
        intent = _score_intent(name, se)
        dom_fit = _score_domain_fit(se)
        fmt_fit = score_format_fit(name, macro, sub)
        dup = _score_duplication(name, candidate.normalized_name, macro, domain_index)
        aud_fit = _score_audience_fit(se)
        fmt_style = _score_format_style(name, se)
        compound_boost = _score_compound_kdp_boost(name, se)
        generic_penalty = _score_generic_pattern_penalty(name)

        pre_val = int(
            nat * 0.15 + spec * 0.20 + intent * 0.15 +
            dom_fit * 0.10 + fmt_fit * 0.10 - dup * 0.10 +
            aud_fit * 0.10 + fmt_style * 0.10
        )
        # Apply compound boost and generic penalty directly for real impact
        pre_val += compound_boost + generic_penalty
        pre_val = max(0, min(100, pre_val))
        # ── Queued Gating: prevent old broad/template candidates from entering queue ──
        canonical = str(se.get("canonical_micro_domain") or se.get("micro_domain") or "")
        is_canonical = False
        if canonical:
            is_canonical = normalize_entity_name(name) == normalize_entity_name(canonical)

        # Rule 1: "Hilfe bei"/"Schritt-für-Schritt" suffix variants → never queued (unconditional)
        is_suffix_variant = "hilfe bei" in name.lower() or "schritt-für-schritt" in name.lower()
        if is_suffix_variant and pre_val >= 70:
            pre_val = 69

        # Rule 2: Explicitly marked non-queue-eligible → max manual_review
        queue_eligible = se.get("queue_eligible", True)
        if queue_eligible is False and pre_val >= 70:
            pre_val = 69

        # Rule 3: For micro-domain-sourced candidates, only the canonical version is queue-eligible.
        if canonical and not is_canonical and pre_val >= 70:
            pre_val = 69

        # Rule 4: No canonical_micro_domain (bulk composer, etc.) → max manual_review
        if not canonical and pre_val >= 70:
            pre_val = 69

        # Rule 5: High duplication (fresh score) → cap score (canonical exempt)
        if isinstance(dup, (int, float)) and dup >= 80 and not is_canonical:
            pre_val = min(pre_val, 59)

        # Rule 6: Medium duplication (fresh score) → max manual_review (canonical exempt)
        if isinstance(dup, (int, float)) and dup >= 50 and not is_canonical and pre_val >= 70:
            pre_val = 69

        # Rule 7: Too many words → downgrade
        if len(name.split()) > 8 and pre_val >= 70:
            pre_val = 69

        all_scores.append(pre_val)
        top_score = max(top_score, pre_val)

        # Calibrated thresholds: 70+ queued, 60-69 manual_review, <60 rejected
        status = "rejected_pre_validation"
        if pre_val >= 70:
            if max_per_macro_domain and macro and macro_counts.get(macro, 0) >= max_per_macro_domain:
                status = "manual_review"
            elif max_per_subdomain and sub and sub_counts.get(sub, 0) >= max_per_subdomain:
                status = "manual_review"
            elif max_per_micro_domain and micro and micro_counts.get(micro, 0) >= max_per_micro_domain:
                status = "manual_review"
            else:
                status = "queued"
                macro_counts[macro] = macro_counts.get(macro, 0) + 1
                sub_counts[sub] = sub_counts.get(sub, 0) + 1
                micro_counts[micro] = micro_counts.get(micro, 0) + 1
        elif pre_val >= 60:
            status = "manual_review"
        else:
            status = "rejected_pre_validation"

        if status == "queued":
            queued += 1
        elif status == "manual_review":
            manual_review += 1
        else:
            rejected += 1

        new_se = dict(se)
        new_se["pre_validation_score"] = pre_val
        new_se["naturalness_score"] = nat
        new_se["specificity_score"] = spec
        new_se["intent_score"] = intent
        new_se["domain_fit_score"] = dom_fit
        new_se["format_fit_score"] = fmt_fit
        new_se["duplication_score"] = dup
        new_se["audience_fit_score"] = aud_fit
        new_se["format_style_score"] = fmt_style
        new_se["validation_queue_status"] = status
        new_se["validation_priority"] = pre_val
        candidate.source_entities = new_se

    db.commit()
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

    return RankResult(
        ranked=len(candidates),
        queued=queued,
        manual_review=manual_review,
        rejected_pre_validation=rejected,
        top_score=top_score,
        avg_score=round(avg_score, 1),
    )
