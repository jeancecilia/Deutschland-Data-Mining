from __future__ import annotations

from datetime import date
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.niche import NicheCluster, NicheClusterBook, OpportunityScore
from app.models.report import SachbuchOpportunityScore, SachbuchTopicGap
from app.models.review import ReviewCluster
from app.schemas.sachbuch import (
    SachbuchAnalysisRead,
    SachbuchOpportunityScoreRead,
    SachbuchTopicGapRead,
)
from app.services.book_classification import infer_book_class
from app.services.market_intelligence import (
    build_competitor_profile,
    infer_cover_direction,
    infer_listing_target_audience,
)
from app.services.sachbuch_scoring import SachbuchScorecard, compute_sachbuch_scorecard
from app.services.scoring_engine import clamp as _clamp, keyword_complexity_risk as _keyword_complexity_risk
from app.services.signal_generation import build_sachbuch_signals
from app.services.text_utils import normalize_text


def analyze_sachbuch_cluster(db: Session, cluster_id: int) -> SachbuchAnalysisRead:
    cluster = db.get(NicheCluster, cluster_id)
    if cluster is None:
        raise ValueError("Cluster not found.")

    latest_score = _get_latest_generic_score(db, cluster.id)
    books, review_clusters = _get_cluster_books_and_reviews(db, cluster.id)
    class_inference = infer_book_class(
        cluster.main_keyword or cluster.name,
        books,
        review_clusters,
        declared_book_type=cluster.book_class,
    )
    cluster.book_class = class_inference.book_class

    topic_gap = _build_topic_gap(cluster, latest_score, books, review_clusters)
    db.add(topic_gap)
    db.flush()

    scorecard = _build_sachbuch_scorecard(cluster, latest_score, books, review_clusters, topic_gap)
    persisted_score = SachbuchOpportunityScore(
        niche_cluster_id=cluster.id,
        german_demand_signal=scorecard.german_demand_signal,
        topic_gap_signal=scorecard.topic_gap_signal,
        depth_weakness_signal=scorecard.depth_weakness_signal,
        freshness_need_signal=scorecard.freshness_need_signal,
        localization_signal=scorecard.localization_signal,
        differentiation_signal=scorecard.differentiation_signal,
        evergreen_potential_signal=scorecard.evergreen_potential_signal,
        monetization_potential_signal=scorecard.monetization_potential_signal,
        authority_risk=scorecard.authority_risk,
        research_effort_risk=scorecard.research_effort_risk,
        liability_risk=scorecard.liability_risk,
        update_risk=scorecard.update_risk,
        publisher_dominance_risk=scorecard.publisher_dominance_risk,
        review_wall_risk=scorecard.review_wall_risk,
        final_score=scorecard.final_score,
        explanation=scorecard.explanation,
    )
    db.add(persisted_score)
    db.commit()
    db.refresh(topic_gap)
    db.refresh(persisted_score)

    return _build_sachbuch_analysis(
        cluster,
        latest_score,
        topic_gap,
        persisted_score,
        books,
        review_clusters,
        class_inference,
    )


def get_latest_sachbuch_analysis(db: Session, cluster_id: int) -> SachbuchAnalysisRead:
    cluster = db.get(NicheCluster, cluster_id)
    if cluster is None:
        raise ValueError("Cluster not found.")

    latest_score = _get_latest_generic_score(db, cluster.id)
    topic_gap = db.scalars(
        select(SachbuchTopicGap)
        .where(SachbuchTopicGap.niche_cluster_id == cluster.id)
        .order_by(SachbuchTopicGap.created_at.desc(), SachbuchTopicGap.id.desc())
    ).first()
    if topic_gap is None:
        raise ValueError("Cluster has no sachbuch analysis yet.")

    sachbuch_score = db.scalars(
        select(SachbuchOpportunityScore)
        .where(SachbuchOpportunityScore.niche_cluster_id == cluster.id)
        .order_by(SachbuchOpportunityScore.created_at.desc(), SachbuchOpportunityScore.id.desc())
    ).first()
    if sachbuch_score is None:
        raise ValueError("Cluster has no stored sachbuch opportunity score yet.")

    books, review_clusters = _get_cluster_books_and_reviews(db, cluster.id)
    class_inference = infer_book_class(
        cluster.main_keyword or cluster.name,
        books,
        review_clusters,
        declared_book_type=cluster.book_class,
    )
    return _build_sachbuch_analysis(
        cluster,
        latest_score,
        topic_gap,
        sachbuch_score,
        books,
        review_clusters,
        class_inference,
    )


def _get_latest_generic_score(db: Session, cluster_id: int) -> OpportunityScore:
    latest_score = db.scalars(
        select(OpportunityScore)
        .where(OpportunityScore.niche_cluster_id == cluster_id)
        .order_by(OpportunityScore.created_at.desc(), OpportunityScore.id.desc())
    ).first()
    if latest_score is None:
        raise ValueError("Cluster has no stored opportunity score.")
    return latest_score


def _get_cluster_books_and_reviews(
    db: Session,
    cluster_id: int,
) -> tuple[list[Book], list[ReviewCluster]]:
    book_rows = db.execute(
        select(NicheClusterBook, Book)
        .join(Book, NicheClusterBook.book_id == Book.id)
        .where(NicheClusterBook.niche_cluster_id == cluster_id)
        .order_by(NicheClusterBook.relevance_score.desc().nullslast(), Book.id.asc())
    ).all()
    books = [book for _, book in book_rows[:12]]
    review_clusters = (
        list(
            db.scalars(
                select(ReviewCluster)
                .where(ReviewCluster.book_id.in_([book.id for book in books]))
                .order_by(ReviewCluster.frequency.desc().nullslast(), ReviewCluster.id.asc())
            )
        )
        if books
        else []
    )
    return books, review_clusters


def _build_sachbuch_scorecard(
    cluster: NicheCluster,
    latest_score: OpportunityScore,
    books: list[Book],
    review_clusters: list[ReviewCluster],
    topic_gap: SachbuchTopicGap,
) -> SachbuchScorecard:
    publishers = [(book.publisher or "unknown").strip().casefold() for book in books if book.publisher]
    publisher_counts: dict[str, int] = {}
    for publisher in publishers:
        publisher_counts[publisher] = publisher_counts.get(publisher, 0) + 1
    publisher_dominance = _clamp(
        (max(publisher_counts.values(), default=0) / max(1, len(books))) * 100
    )
    return compute_sachbuch_scorecard(
        keyword_text=cluster.main_keyword or cluster.name,
        books=books,
        review_clusters=review_clusters,
        topic_gap=topic_gap,
        generic_demand_score=latest_score.demand_score or 0,
        generic_differentiation_score=latest_score.differentiation_score or 0,
        generic_authority_risk=latest_score.authority_risk or 0,
        generic_research_effort_score=latest_score.research_effort_score or 0,
        generic_review_wall_risk=latest_score.review_wall_risk or 0,
        publisher_dominance_risk=publisher_dominance,
    )


def _build_sachbuch_analysis(
    cluster: NicheCluster,
    latest_score: OpportunityScore,
    topic_gap: SachbuchTopicGap,
    sachbuch_score: SachbuchOpportunityScore,
    books: list[Book],
    review_clusters: list[ReviewCluster],
    class_inference: object,
) -> SachbuchAnalysisRead:
    keyword = cluster.main_keyword or cluster.name
    score_warnings = _quality_warnings_from_persisted_score(sachbuch_score)
    audience = _recommended_target_audience(keyword, books, review_clusters)
    analysis = SachbuchAnalysisRead(
        niche_cluster_id=cluster.id,
        niche_cluster_name=cluster.name,
        main_keyword=keyword,
        opportunity_score=latest_score.final_score,
        sachbuch_score=SachbuchOpportunityScoreRead(
            german_demand_signal=sachbuch_score.german_demand_signal,
            topic_gap_signal=sachbuch_score.topic_gap_signal,
            depth_weakness_signal=sachbuch_score.depth_weakness_signal,
            freshness_need_signal=sachbuch_score.freshness_need_signal,
            localization_signal=sachbuch_score.localization_signal,
            differentiation_signal=sachbuch_score.differentiation_signal,
            evergreen_potential_signal=sachbuch_score.evergreen_potential_signal,
            monetization_potential_signal=sachbuch_score.monetization_potential_signal,
            authority_risk=sachbuch_score.authority_risk,
            research_effort_risk=sachbuch_score.research_effort_risk,
            liability_risk=sachbuch_score.liability_risk,
            update_risk=sachbuch_score.update_risk,
            publisher_dominance_risk=sachbuch_score.publisher_dominance_risk,
            review_wall_risk=sachbuch_score.review_wall_risk,
            final_score=sachbuch_score.final_score,
            explanation=sachbuch_score.explanation,
            quality_warnings=score_warnings,
        ),
        go_decision=_go_decision(sachbuch_score, topic_gap),
        inferred_book_class=class_inference.book_class,
        book_class_confidence=class_inference.confidence,
        classification_evidence=class_inference.evidence,
        recommended_target_audience=audience,
        reader_problem=_reader_problem(keyword, topic_gap, audience),
        reader_promise=_reader_promise(keyword, topic_gap, audience),
        why_now=_why_now(keyword, topic_gap, sachbuch_score),
        subtitle_ideas=_subtitle_ideas(keyword, topic_gap, audience),
        positioning_angles=_positioning_angles(keyword, topic_gap),
        differentiation_opportunities=_differentiation_opportunities(review_clusters, topic_gap),
        chapter_blueprint=_chapter_blueprint(keyword, review_clusters),
        subchapter_blueprint=_subchapter_blueprint(keyword, topic_gap),
        practice_modules=_practice_modules(keyword, topic_gap),
        checklist_ideas=_checklist_ideas(keyword, topic_gap),
        case_study_ideas=_case_study_ideas(keyword, audience),
        glossary_terms=_glossary_terms(keyword, books),
        research_questions=_research_questions(keyword, topic_gap),
        backend_keywords=_backend_keywords(keyword),
        category_strategy=_category_strategy(keyword, books, topic_gap),
        source_requirements=_source_requirements(keyword, topic_gap),
        expert_needs=_expert_needs(topic_gap, sachbuch_score),
        quality_warnings=score_warnings,
        cover_direction=infer_cover_direction(keyword, class_inference.book_class, audience),
        target_length=_target_length(books, sachbuch_score),
        writing_effort=_writing_effort(sachbuch_score),
        topic_gap=SachbuchTopicGapRead.model_validate(topic_gap),
    )
    return analysis.model_copy(update={"signals": build_sachbuch_signals(analysis)})


def _build_topic_gap(
    cluster: NicheCluster,
    score: OpportunityScore,
    books: list[Book],
    review_clusters: list[ReviewCluster],
) -> SachbuchTopicGap:
    publication_years = [book.publication_date.year for book in books if book.publication_date is not None]
    current_year = date.today().year
    avg_age = mean([max(0, current_year - year) for year in publication_years]) if publication_years else 0
    outdated_content_signal = _clamp(
        round(avg_age * 10 + _count_matches(_book_texts(books), ["aktualisiert", "auflage", "2024", "2025", "2026"]) * 4)
    )

    negative_text = " ".join(_review_texts(review_clusters)).casefold()
    missing_examples_signal = _clamp(
        20 + _count_matches([negative_text], ["beispiel", "praxis", "konkret", "oberflächlich", "allgemein"]) * 12
    )
    missing_checklists_signal = _clamp(
        15 + _count_matches([negative_text], ["checkliste", "vorlage", "template", "schritt", "anleitung"]) * 12
    )
    localization_gap_signal = _clamp(
        15
        + _count_matches(
            [negative_text] + _book_texts(books),
            ["deutschland", "deutsch", "lokal", "amerikanisch", "übersetzung", "dsgvo"],
        )
        * 10
    )

    page_counts = [book.page_count for book in books if book.page_count]
    avg_page_count = mean(page_counts) if page_counts else 0
    shallow_review_hits = _count_matches([negative_text], ["oberflächlich", "allgemein", "theoretisch", "ki"])
    content_depth_score = _clamp(round(55 + min(22, avg_page_count / 12) - shallow_review_hits * 8))

    keyword_text = (cluster.main_keyword or cluster.name).casefold()
    complexity_risk = _keyword_complexity_risk(keyword_text)
    authority_required = complexity_risk >= 45
    expert_review_required = complexity_risk >= 60 or any(
        term in keyword_text
        for term in ["medizin", "gesundheit", "recht", "steuer", "finanz", "investment", "therapie"]
    )

    summary = (
        f"Cluster {cluster.name} shows a generic opportunity score of {score.final_score or 0}. "
        f"Average publication age is {avg_age:.1f} years, content depth is {content_depth_score}, "
        f"and the largest attack surfaces are examples ({missing_examples_signal}), "
        f"checklists ({missing_checklists_signal}) and localization ({localization_gap_signal})."
    )

    return SachbuchTopicGap(
        niche_cluster_id=cluster.id,
        topic_gap_summary=summary,
        outdated_content_signal=outdated_content_signal,
        missing_examples_signal=missing_examples_signal,
        missing_checklists_signal=missing_checklists_signal,
        localization_gap_signal=localization_gap_signal,
        content_depth_score=content_depth_score,
        authority_required=authority_required,
        expert_review_required=expert_review_required,
    )


def _recommended_target_audience(
    keyword: str,
    books: list[Book],
    review_clusters: list[ReviewCluster],
) -> str:
    normalized_keyword = normalize_text(keyword) or keyword
    audience_hits = [
        infer_listing_target_audience(book)
        for book in books[:5]
    ]
    audiences = [audience for audience in audience_hits if audience]
    if audiences:
        return audiences[0]
    lowered = normalized_keyword.casefold()
    if "für " in lowered:
        return normalized_keyword.split("für ", 1)[1].strip().capitalize()
    if "selbst" in lowered or "betrieb" in lowered:
        return "Selbstständige und kleine Betriebe"
    if "senior" in lowered:
        return "Seniorinnen und Senioren"
    if review_clusters:
        profile = build_competitor_profile(normalized_keyword, books[0], review_clusters[:6]) if books else None
        if profile and profile.actual_target_audience:
            return profile.actual_target_audience
    return f"Deutschsprachige Käufer mit konkretem Bedarf rund um {normalized_keyword}"


def _reader_problem(keyword: str, topic_gap: SachbuchTopicGap, audience: str) -> str:
    normalized_keyword = normalize_text(keyword) or keyword
    if (topic_gap.localization_gap_signal or 0) >= 35:
        return f"{audience} finden zu {normalized_keyword} zwar Literatur, aber zu wenig lokal passende und umsetzbare Orientierung für Deutschland."
    return f"{audience} finden im sichtbaren Markt zu {normalized_keyword} zu wenig klare, praktische und sauber strukturierte Hilfe."


def _reader_promise(keyword: str, topic_gap: SachbuchTopicGap, audience: str) -> str:
    normalized_keyword = normalize_text(keyword) or keyword
    promise = f"Ein praxisnahes Deutschland-Buch zu {normalized_keyword}, das {audience} schneller von der Orientierung in die Anwendung bringt."
    if (topic_gap.missing_checklists_signal or 0) >= 35:
        promise += " Checklisten, Vorlagen und konkrete Arbeitsschritte sind fester Kern des Nutzens."
    return promise


def _why_now(keyword: str, topic_gap: SachbuchTopicGap, sachbuch_score: SachbuchOpportunityScore) -> str:
    reasons = []
    if (topic_gap.outdated_content_signal or 0) >= 35:
        reasons.append("sichtbare Konkurrenztitel altern inhaltlich")
    if (topic_gap.localization_gap_signal or 0) >= 35:
        reasons.append("Deutschland-Bezug ist im Markt unzureichend bedient")
    if (sachbuch_score.update_risk or 0) >= 35:
        reasons.append("das Thema verändert sich schnell genug, dass aktuelle Praxisführung zählt")
    if not reasons:
        reasons.append("es gibt Raum für klarere Positionierung und bessere Nutzbarkeit")
    return f"Jetzt relevant, weil {', '.join(reasons)}."


def _subtitle_ideas(keyword: str, topic_gap: SachbuchTopicGap, audience: str) -> list[str]:
    return [
        f"Praxiswissen für {audience} mit klaren Deutschland-Beispielen",
        "Mit Checklisten, Vorlagen und direkt umsetzbaren Praxisbausteinen",
        (
            "Aktuell, lokal verständlich und ohne unnötigen Theorieballast"
            if (topic_gap.localization_gap_signal or 0) >= 25
            else "Klar strukturiert, verständlich erklärt und sofort anwendbar"
        ),
    ]


def _positioning_angles(keyword: str, topic_gap: SachbuchTopicGap) -> list[str]:
    angles = [
        "deutschland-spezifische Umsetzung statt generischer Übersetzung",
        "mehr Praxisnutzen und weniger abstrakte Theorie",
        "zielgruppenspezifische Beispiele statt breiter Massenansprache",
    ]
    if (topic_gap.missing_checklists_signal or 0) >= 35:
        angles.append("umsetzungsorientiertes Arbeitsbuch mit Checklisten und Vorlagen")
    return angles[:4]


def _differentiation_opportunities(
    review_clusters: list[ReviewCluster],
    topic_gap: SachbuchTopicGap,
) -> list[str]:
    opportunities: list[str] = []
    cluster_names = " ".join(cluster.cluster_name for cluster in review_clusters).casefold()

    if topic_gap.missing_examples_signal and topic_gap.missing_examples_signal >= 45:
        opportunities.append("Mehr konkrete Praxisbeispiele und echte Anwendungsszenarien liefern.")
    if topic_gap.missing_checklists_signal and topic_gap.missing_checklists_signal >= 45:
        opportunities.append("Checklisten, Vorlagen und Schritt-für-Schritt-Bausteine ergänzen.")
    if topic_gap.localization_gap_signal and topic_gap.localization_gap_signal >= 40:
        opportunities.append("Deutschland-spezifische Prozesse, Begriffe und Alltagssituationen einbauen.")
    if "general_feedback" in cluster_names or not opportunities:
        opportunities.append("Die Zielgruppe enger zuschneiden und das Nutzenversprechen klarer formulieren.")

    return opportunities[:4]


def _chapter_blueprint(keyword: str, review_clusters: list[ReviewCluster]) -> list[str]:
    normalized_keyword = normalize_text(keyword) or keyword
    blueprint = [
        f"Einführung: Warum {normalized_keyword} im deutschen Markt relevant ist",
        "Grundlagen: Begriffe, typische Fehler und Zielgruppenkontext",
        "Praxis: Schritt-für-Schritt-System mit konkreten Beispielen",
        "Vorlagen und Checklisten: direkt nutzbare Umsetzungshilfen",
        "Sonderfälle: häufige Fragen, Stolperfallen und Anpassungen",
        "Abschluss: nächste Schritte, Ressourcen und Qualitätssicherung",
    ]
    cluster_text = " ".join(_review_texts(review_clusters)).casefold()
    if "beispiel" in cluster_text:
        blueprint[2] = "Praxis: mehrere vollständige Fallbeispiele mit konkreten Entscheidungen"
    if "struktur" in cluster_text or "layout" in cluster_text:
        blueprint[1] = "Grundlagen: klare Struktur, Entscheidungslogik und Leserführung"
    return blueprint


def _subchapter_blueprint(keyword: str, topic_gap: SachbuchTopicGap) -> list[str]:
    normalized_keyword = normalize_text(keyword) or keyword
    subchapters = [
        f"Problemdefinition und Marktüberblick zu {normalized_keyword}",
        "Typische Anfängerfehler und Fehlannahmen",
        "Werkzeuge, Abläufe und Entscheidungsraster",
        "Praxisbeispiel mit Zwischenschritten und Varianten",
        "Checklisten, Vorlagen und lokale Sonderfälle",
        "Qualitätssicherung, Quellen und Update-Prozess",
    ]
    if (topic_gap.localization_gap_signal or 0) >= 35:
        subchapters.insert(4, "Deutschland-spezifische Regeln, Begriffe oder Kontexte")
    return subchapters[:7]


def _practice_modules(keyword: str, topic_gap: SachbuchTopicGap) -> list[str]:
    modules = [
        f"Praxisfall 1: erster schneller Einsatz von {normalize_text(keyword) or keyword}",
        "Praxisfall 2: typische Fehler vermeiden und sauber korrigieren",
        "Praxisfall 3: Umsetzung im deutschen Arbeitsalltag oder Kundenkontakt",
    ]
    if (topic_gap.localization_gap_signal or 0) >= 30:
        modules.append("Praxisfall 4: Deutschland-spezifische Sonderfälle und Erwartungen")
    return modules[:4]


def _checklist_ideas(keyword: str, topic_gap: SachbuchTopicGap) -> list[str]:
    ideas = [
        "Start-Checkliste für die ersten 7 Tage",
        "Qualitäts- und Plausibilitätscheck vor Veröffentlichung oder Umsetzung",
        "Praxis-Checkliste für wiederkehrende Routinen",
    ]
    if topic_gap.expert_review_required:
        ideas.append("Fachprüfungs-Checkliste vor finaler Freigabe")
    return ideas[:4]


def _case_study_ideas(keyword: str, audience: str) -> list[str]:
    normalized_keyword = normalize_text(keyword) or keyword
    return [
        f"Fallstudie: {audience} startet mit {normalized_keyword} ohne Vorwissen.",
        "Fallstudie: Ein typischer Fehlstart wird analysiert und korrigiert.",
        "Fallstudie: Unterschied zwischen generischer und Deutschland-passender Umsetzung.",
    ]


def _glossary_terms(keyword: str, books: list[Book]) -> list[str]:
    seed_terms = [normalize_text(keyword) or keyword, "Praxisbeispiel", "Checkliste", "Vorlage", "Qualitätssicherung"]
    if books and books[0].title:
        seed_terms.append((normalize_text(books[0].title) or books[0].title).split(":")[0])
    return _unique_non_empty(seed_terms)[:8]


def _research_questions(keyword: str, topic_gap: SachbuchTopicGap) -> list[str]:
    questions = [
        f"Welche Deutschland-spezifischen Rahmenbedingungen müssen für {normalize_text(keyword) or keyword} erklärt werden?",
        "Welche Praxisbeispiele fehlen im sichtbaren Wettbewerbsumfeld am häufigsten?",
        "Welche Einwände, Missverständnisse oder Stolperfallen sollte das Buch direkt entschärfen?",
    ]
    if topic_gap.authority_required:
        questions.append("Welche Primärquellen oder offiziellen Leitfäden müssen verbindlich geprüft werden?")
    return questions[:4]


def _backend_keywords(keyword: str) -> list[str]:
    normalized_keyword = normalize_text(keyword) or keyword
    base = normalized_keyword.casefold()
    suggestions = [
        normalized_keyword,
        f"{normalized_keyword} praxis",
        f"{normalized_keyword} ratgeber",
        f"{normalized_keyword} vorlagen",
        f"{normalized_keyword} checklisten",
    ]
    if "für " in base:
        audience = normalized_keyword.split("für ", 1)[1].strip()
        suggestions.append(f"{audience} praxis")
        suggestions.append(f"{audience} leitfaden")
    return _unique_non_empty(suggestions)[:7]


def _category_strategy(keyword: str, books: list[Book], topic_gap: SachbuchTopicGap) -> list[str]:
    normalized_keyword = normalize_text(keyword) or keyword
    visible_categories = _unique_non_empty(
        [
            book.primary_category
            for book in books
            if book.primary_category
        ]
        + [
            book.secondary_category
            for book in books
            if book.secondary_category
        ]
    )
    strategy = [
        f"Primärkategorie nah am Kernproblem von '{normalized_keyword}' wählen, nicht zu breit in 'Allgemeines'.",
        "Sekundärkategorie mit klarer Praxis- oder Berufsrelevanz nutzen, um Sichtbarkeit gegen generische Titel zu verbessern.",
        f"Sichtbare Kategoriecluster: {', '.join(visible_categories[:3]) if visible_categories else 'noch zu wenig sauber extrahiert'}.",
    ]
    if (topic_gap.localization_gap_signal or 0) >= 30:
        strategy.append("Metadaten auf Deutschland-Bezug und lokale Nutzbarkeit ausrichten.")
    return strategy[:4]


def _source_requirements(keyword: str, topic_gap: SachbuchTopicGap) -> list[str]:
    lowered = keyword.casefold()
    requirements = ["Alle Behauptungen aus gespeicherten Marktdaten und sichtbaren Quellen ableiten."]
    if topic_gap.authority_required:
        requirements.append("Aktuelle Primärquellen oder offizielle Leitfäden einplanen.")
    if topic_gap.expert_review_required:
        requirements.append("Fachprüfung vor Veröffentlichung verbindlich vorsehen.")
    if any(term in lowered for term in ["gesund", "medizin", "therapie"]):
        requirements.append("Keine Heilversprechen; medizinische Aussagen separat prüfen.")
    if any(term in lowered for term in ["recht", "steuer", "finanz", "investment"]):
        requirements.append(
            "Rechts-, Steuer- oder Finanzhinweise nur mit sauberem Disclaimer und Quellenbezug formulieren."
        )
    return requirements


def _expert_needs(topic_gap: SachbuchTopicGap, sachbuch_score: SachbuchOpportunityScore) -> list[str]:
    needs = []
    if topic_gap.authority_required:
        needs.append("Belastbare Primärquellen oder offizielle Leitfäden")
    if topic_gap.expert_review_required or (sachbuch_score.liability_risk or 0) >= 60:
        needs.append("Externe Fachprüfung vor Veröffentlichung")
    if (sachbuch_score.update_risk or 0) >= 35:
        needs.append("Klar definierter Update- und Editionsprozess")
    return needs or ["Keine außergewöhnlichen Expertenanforderungen über saubere Quellenarbeit hinaus."]


def _quality_warnings_from_persisted_score(score: SachbuchOpportunityScore) -> list[str]:
    warnings: list[str] = []
    if (score.liability_risk or 0) >= 60:
        warnings.append("Haftungs- oder Beratungsrisiko ist erhöht; Aussagen nur mit sauberem Disclaimer und Quellenbezug.")
    if (score.authority_risk or 0) >= 55:
        warnings.append("Fachprüfung oder belastbare Primärquellen sollten vor Veröffentlichung eingeplant werden.")
    if (score.update_risk or 0) >= 40:
        warnings.append("Das Thema hat erhöhten Aktualisierungsdruck; Editionen und Update-Prozess mitdenken.")
    if (score.publisher_dominance_risk or 0) >= 55:
        warnings.append("Starke Verlags- oder Markenballung erschwert die Positionierung gegen etablierte Titel.")
    return warnings


def _target_length(books: list[Book], sachbuch_score: SachbuchOpportunityScore) -> str:
    page_counts = [book.page_count for book in books if book.page_count]
    avg_pages = mean(page_counts) if page_counts else 0
    if avg_pages >= 180 or (sachbuch_score.research_effort_risk or 0) >= 55:
        return "ca. 180-240 Seiten"
    if avg_pages >= 120:
        return "ca. 140-190 Seiten"
    return "ca. 110-160 Seiten"


def _writing_effort(sachbuch_score: SachbuchOpportunityScore) -> str:
    effort = sachbuch_score.research_effort_risk or 0
    if effort >= 70:
        return "hoch"
    if effort >= 45:
        return "mittel bis hoch"
    return "mittel"


def _go_decision(sachbuch_score: SachbuchOpportunityScore, topic_gap: SachbuchTopicGap) -> str:
    final_score = sachbuch_score.final_score or 0
    if topic_gap.expert_review_required and final_score < 72:
        return "MAYBE"
    if final_score >= 68 and (sachbuch_score.liability_risk or 0) < 70:
        return "GO"
    if final_score >= 45:
        return "MAYBE"
    return "NO-GO"


def _count_matches(texts: list[str], needles: list[str]) -> int:
    haystack = " ".join(texts).casefold()
    return sum(1 for needle in needles if needle in haystack)


def _book_texts(books: list[Book]) -> list[str]:
    return [
        " ".join(
            part
            for part in [
                book.title,
                book.subtitle,
                book.description,
                book.publisher,
                book.primary_category,
                book.secondary_category,
                book.table_of_contents,
            ]
            if part
        )
        for book in books
    ]


def _review_texts(review_clusters: list[ReviewCluster]) -> list[str]:
    return [
        " ".join(
            part
            for part in [
                cluster.cluster_name,
                cluster.summary,
                cluster.example_snippets,
                cluster.suggested_improvements,
            ]
            if part
        )
        for cluster in review_clusters
    ]


def _unique_non_empty(values: list[str | None]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized_value = (normalize_text(value) or "").strip()
        if not normalized_value or normalized_value in seen:
            continue
        seen.add(normalized_value)
        output.append(normalized_value)
    return output
