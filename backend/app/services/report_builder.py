from __future__ import annotations

import csv
import json
from pathlib import Path
from textwrap import wrap

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.niche import NicheCluster, NicheClusterBook, OpportunityScore
from app.models.report import Report
from app.schemas.analysis import NicheClusterAnalysisRead
from app.schemas.report import ReportRead
from app.schemas.sachbuch import SachbuchAnalysisRead
from app.services.ai_intelligence import build_report_synthesis
from app.services.signal_generation import build_cluster_signals
from app.services.text_utils import normalize_text


REPORTS_DIR = Path(__file__).resolve().parents[2] / "generated_reports"
SUPPORTED_REPORT_TYPES = {
    "niche_report",
    "sachbuch_opportunity_report",
    "book_concept_report",
    "keyword_report",
    "competitor_report",
    "go_no_go_report",
}


def generate_cluster_report(
    db: Session,
    cluster_id: int,
    report_type: str = "niche_report",
) -> ReportRead:
    cluster = db.get(NicheCluster, cluster_id)
    if cluster is None:
        raise ValueError("Cluster not found.")

    if report_type == "niche_report" and cluster.book_class == "sachbuch":
        report_type = "sachbuch_opportunity_report"
    if report_type not in SUPPORTED_REPORT_TYPES:
        raise ValueError(f"Unsupported report type: {report_type}")

    latest_score = db.scalars(
        select(OpportunityScore)
        .where(OpportunityScore.niche_cluster_id == cluster.id)
        .order_by(OpportunityScore.created_at.desc(), OpportunityScore.id.desc())
    ).first()
    if latest_score is None:
        raise ValueError("Cluster has no stored opportunity score.")

    from app.services.niche_cluster_analysis import get_cluster_analysis
    from app.services.sachbuch_analysis import analyze_sachbuch_cluster, get_latest_sachbuch_analysis

    cluster_analysis = get_cluster_analysis(db, cluster.id)
    sachbuch_analysis: SachbuchAnalysisRead | None = None
    if report_type != "niche_report" or cluster.book_class == "sachbuch":
        try:
            sachbuch_analysis = get_latest_sachbuch_analysis(db, cluster.id)
        except ValueError:
            sachbuch_analysis = analyze_sachbuch_cluster(db, cluster.id)

    book_rows = db.execute(
        select(NicheClusterBook, Book)
        .join(Book, NicheClusterBook.book_id == Book.id)
        .where(NicheClusterBook.niche_cluster_id == cluster.id)
        .order_by(NicheClusterBook.relevance_score.desc().nullslast(), Book.id.asc())
    ).all()
    books = [book for _, book in book_rows]

    context = _build_report_context(cluster, cluster_analysis, sachbuch_analysis)
    markdown_content = _build_markdown_report(report_type, context)
    artifact_paths = _write_report_artifacts(
        cluster=cluster,
        latest_score=latest_score,
        books=books,
        cluster_analysis=cluster_analysis,
        sachbuch_analysis=sachbuch_analysis,
        markdown_content=markdown_content,
        report_type=report_type,
        context=context,
    )
    status = "generated" if artifact_paths["pdf"] is not None else "generated_without_pdf"

    report = db.scalars(
        select(Report)
        .where(
            Report.niche_cluster_id == cluster.id,
            Report.report_type == report_type,
        )
        .order_by(Report.updated_at.desc(), Report.id.desc())
    ).first()
    if report is None:
        report = Report(
            niche_cluster_id=cluster.id,
            report_type=report_type,
            status=status,
        )
    report.title = f"{cluster.name} Report"
    report.markdown_content = markdown_content
    report.markdown_path = str(artifact_paths["markdown"])
    report.pdf_path = str(artifact_paths["pdf"]) if artifact_paths["pdf"] is not None else None
    report.csv_path = str(artifact_paths["csv"])
    report.json_path = str(artifact_paths["json"])
    report.status = status
    db.add(report)
    db.commit()
    db.refresh(report)
    return ReportRead.model_validate(report)


def list_reports(db: Session) -> list[ReportRead]:
    reports = list(db.scalars(select(Report).order_by(Report.updated_at.desc(), Report.id.desc())))
    latest_by_key: dict[tuple[int, str], Report] = {}
    for report in reports:
        key = (report.niche_cluster_id, report.report_type)
        if key in latest_by_key:
            continue
        latest_by_key[key] = report
    return [ReportRead.model_validate(report) for report in latest_by_key.values()]


def get_report(db: Session, report_id: int) -> ReportRead:
    report = db.get(Report, report_id)
    if report is None:
        raise ValueError("Report not found.")
    return ReportRead.model_validate(report)


def _build_report_context(
    cluster: NicheCluster,
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
) -> dict[str, object]:
    competitor_books = cluster_analysis.competitor_books[:10]
    recommendation = (
        sachbuch_analysis.go_decision
        if sachbuch_analysis
        else _generic_recommendation(cluster_analysis.score.final_score or 0)
    )
    synthesis = build_report_synthesis(cluster_analysis, sachbuch_analysis)
    signals = build_cluster_signals(cluster_analysis, sachbuch_analysis)

    return {
        "cluster": {
            "id": cluster.id,
            "name": cluster.name,
            "main_keyword": cluster.main_keyword,
            "marketplace": cluster.marketplace,
            "language": cluster.language,
            "book_class": cluster.book_class,
            "status": cluster.status,
        },
        "cluster_analysis": cluster_analysis.model_dump(),
        "sachbuch_analysis": sachbuch_analysis.model_dump() if sachbuch_analysis else None,
        "recommendation": recommendation,
        "report_synthesis": synthesis.model_dump(),
        "signals": [signal.model_dump() for signal in signals],
        "metadata_strategy": _metadata_strategy(cluster_analysis, sachbuch_analysis),
        "competitor_findings": _competitor_findings(cluster_analysis),
        "competition_table": _competition_table(competitor_books),
        "bsr_indicator_lines": _bsr_indicator_lines(competitor_books),
        "saturation_lines": _saturation_lines(cluster_analysis),
        "risk_lines": _risk_lines(cluster_analysis, sachbuch_analysis),
    }


def _build_markdown_report(report_type: str, context: dict[str, object]) -> str:
    if report_type == "keyword_report":
        return _build_keyword_report(context)
    if report_type == "competitor_report":
        return _build_competitor_report(context)
    if report_type == "book_concept_report":
        return _build_book_concept_report(context)
    if report_type == "go_no_go_report":
        return _build_go_no_go_report(context)
    return _build_full_niche_report(report_type, context)


def _build_full_niche_report(report_type: str, context: dict[str, object]) -> str:
    cluster = context["cluster"]
    detail = context["cluster_analysis"]
    sachbuch = context["sachbuch_analysis"]
    synthesis = context["report_synthesis"]
    heading = (
        f"Sachbuch Opportunity Report: {cluster['main_keyword'] or cluster['name']}"
        if report_type == "sachbuch_opportunity_report"
        else f"KDP Nischenreport: {cluster['main_keyword'] or cluster['name']}"
    )
    executive_score = (
        sachbuch["sachbuch_score"]["final_score"]
        if sachbuch
        else detail["score"]["final_score"]
    )
    product_target = (
        sachbuch["recommended_target_audience"]
        if sachbuch
        else ", ".join(detail["audience_hints"][:2]) if detail["audience_hints"] else "Deutschsprachige Kaeufer mit klarer Nutzungssituation"
    )
    product_promise = (
        sachbuch["reader_promise"]
        if sachbuch
        else "Klares Nutzenversprechen mit besserer deutscher Umsetzung."
    )
    product_positioning = sachbuch["positioning_angles"] if sachbuch else context["metadata_strategy"]
    product_differentiation = (
        sachbuch["differentiation_opportunities"]
        if sachbuch
        else detail["top_opportunities"]
    )

    return f"""# {heading}

## 15.1 Executive Summary

```text
Nische: {cluster['name']}
Marketplace: {cluster['marketplace']}
Sprache: {cluster['language']}
Buchklasse: {detail['recommended_book_class']}
Hauptkeyword: {detail['main_keyword']}
Opportunity Score: {executive_score}/100
Empfehlung: {context['recommendation']}
```

Synthese:
{synthesis['executive_summary']}

Signal Snapshot:
{_join_lines(_signal_lines(context['signals']))}

## 15.2 Warum diese Nische interessant ist

Nachfrage-Indikatoren:
{_join_lines([
    f"Demand Score: {detail['score']['demand_score']}",
    detail['score']['explanation'],
])}

BSR-Indikatoren:
{_join_lines(context['bsr_indicator_lines'])}

Keyword-Indikatoren:
{_join_lines([
    f"{detail['keyword_count']} Keywords im Cluster",
    f"Klassifikation: {detail['book_classification']['book_class']} ({detail['book_classification']['confidence']} %)",
    f"Keyword Specificity: {detail['score']['keyword_specificity_score']}",
    f"New Entrant Signal: {detail['score']['new_entrant_signal']}",
])}

Konkurrenz-Indikatoren:
{_join_lines(context['competitor_findings'])}

## 15.3 Wettbewerb

{context['competition_table']}

## 15.4 Saettigungsanalyse

```text
{_join_lines(context['saturation_lines'])}
```

## 15.5 Review Intelligence

Was Kaeufer moegen:
{_join_lines(detail['positive_review_signals'])}

Was Kaeufer kritisieren:
{_join_lines(detail['top_complaints'])}

Was fehlt:
{_join_lines(detail['missing_features'])}

Welche Woerter Kaeufer verwenden:
{_join_lines(detail['buyer_words'])}

Welche Zielgruppe wirklich kauft:
{_join_lines(detail['audience_hints'])}

Verdichtete Luecke:
{synthesis['gap_summary']}

## 15.6 Produktchance

```text
Empfohlener Buchtyp: {detail['recommended_book_class']}
Zielgruppe: {product_target}
Hauptversprechen: {product_promise}
```

Positionierung:
{_join_lines(_unique([*synthesis['positioning_angles'], *product_positioning]))}

Differenzierung:
{_join_lines(product_differentiation)}

## 15.7 Buchstruktur

{_book_structure_section(detail['main_keyword'], sachbuch)}

## 15.8 Keyword-Strategie

```text
Hauptkeywords:
{_join_lines(detail['keyword_strategy']['primary_keywords'])}

Nebenkeywords:
{_join_lines(detail['keyword_strategy']['secondary_keywords'])}

Long-Tail Keywords:
{_join_lines(detail['keyword_strategy']['long_tail_keywords'])}

Backend Keyword Vorschlaege:
{_join_lines(_unique([*detail['keyword_strategy']['backend_keywords'], *synthesis['metadata_strategy']]))}

Keywords vermeiden:
{_join_lines(detail['keyword_strategy']['avoid_keywords'])}

Keyword Cluster:
{_join_lines(detail['keyword_strategy']['keyword_clusters'])}
```

## 15.9 Kategorie-Strategie

```text
Moegliche Kategorien:
{_join_lines(detail['category_strategy']['possible_categories'])}

Kategorie-Relevanz:
{_join_lines(detail['category_strategy']['category_relevance'])}

Kategorie-Risiko:
{_join_lines(detail['category_strategy']['category_risks'])}

Sichtbarkeitschance:
{_join_lines(detail['category_strategy']['visibility_opportunities'])}
```

## 15.10 Risikoanalyse

```text
{_join_lines(context['risk_lines'])}
```

## 15.11 Entscheidung

```text
{context['recommendation']}
```
"""


def _build_keyword_report(context: dict[str, object]) -> str:
    cluster = context["cluster"]
    detail = context["cluster_analysis"]
    synthesis = context["report_synthesis"]
    return f"""# Keyword Report: {cluster['main_keyword'] or cluster['name']}

## Fokus

```text
Seed Keyword: {detail['main_keyword']}
Top Cluster-Keywords:
{_join_lines([item['keyword'] for item in detail['top_keywords'][:10]])}
```

## Signal Snapshot

{_join_lines(_signal_lines(context['signals']))}

## Metadaten-Strategie

```text
{_join_lines(_unique([*context['metadata_strategy'], *synthesis['metadata_strategy']]))}
```

## Keyword-Strategie

```text
Primary:
{_join_lines(detail['keyword_strategy']['primary_keywords'])}

Secondary:
{_join_lines(detail['keyword_strategy']['secondary_keywords'])}

Backend:
{_join_lines(detail['keyword_strategy']['backend_keywords'])}
```

## Kategorie-Strategie

```text
{_join_lines(detail['category_strategy']['visibility_opportunities'])}
```

## Wettbewerbsnahe Keyword-Signale

{_join_lines([book['title'] for book in detail['competitor_books'][:10] if book['title']])}

## Titel-Ideen

{_join_lines(synthesis['title_ideas'])}
"""


def _build_competitor_report(context: dict[str, object]) -> str:
    detail = context["cluster_analysis"]
    sections: list[str] = []
    for book in detail["competitor_books"][:10]:
        sections.append(
            "\n".join(
                [
                    f"### {book['title'] or book['asin']}",
                    f"- ASIN: {book['asin']}",
                    f"- Preis: {book['latest_price'] if book['latest_price'] is not None else 'n/a'}",
                    f"- Reviews: {book['latest_review_count'] if book['latest_review_count'] is not None else 'n/a'}",
                    f"- BSR: {book['bsr']['latest_bsr'] if book['bsr']['latest_bsr'] is not None else 'n/a'} ({book['bsr']['trend']})",
                    f"- Kategorien: {', '.join(book['category_labels']) if book['category_labels'] else 'n/a'}",
                    f"- Zielgruppe laut Listing: {book['listing_target_audience'] or 'n/a'}",
                    f"- Tatsaechliche Zielgruppe laut Reviews: {book['actual_target_audience'] or 'n/a'}",
                    f"- Listing Quality: {book['listing_quality_score']}",
                    f"- Cover Quality: {book['cover_quality_score']}",
                    f"- Content Depth: {book['content_depth_score']}",
                    f"- TOC-Hinweis: {book['table_of_contents_excerpt'] or 'nicht sichtbar'}",
                    f"- Staerken: {', '.join(book['strengths']) if book['strengths'] else 'n/a'}",
                    f"- Schwaechen: {', '.join(book['weaknesses']) if book['weaknesses'] else 'n/a'}",
                    f"- AI Audience: {book['ai_target_audience'] or 'n/a'}",
                    f"- AI Problem: {book['ai_core_problem'] or 'n/a'}",
                    f"- AI Use Case: {book['ai_use_case'] or 'n/a'}",
                    f"- AI Promise: {book['ai_promised_outcome'] or 'n/a'}",
                    f"- AI Summary: {book['semantic_summary'] or 'n/a'}",
                ]
            )
        )

    return f"""# Competitor Report: {detail['main_keyword']}

## Kernerkenntnisse

```text
{_join_lines(context['competitor_findings'])}
```

Synthese:
{context['report_synthesis']['executive_summary']}

## Signal Snapshot

{_join_lines(_signal_lines(context['signals']))}

## Wettbewerber

{'\n\n'.join(sections)}
"""


def _build_book_concept_report(context: dict[str, object]) -> str:
    sachbuch = context["sachbuch_analysis"]
    detail = context["cluster_analysis"]
    if sachbuch is None:
        return f"""# Book Concept Report: {detail['main_keyword']}

Kein Sachbuch-spezifischer Blueprint verfuegbar.

Synthese:
{context['report_synthesis']['blueprint_summary']}
"""

    return f"""# Book Concept Report: {detail['main_keyword']}

## Kernkonzept

```text
Zielgruppe: {sachbuch['recommended_target_audience']}
Problem: {sachbuch['reader_problem']}
Leserversprechen: {sachbuch['reader_promise']}
Warum jetzt: {sachbuch['why_now']}
Go/Maybe/No-Go: {sachbuch['go_decision']}
```

## Signal Snapshot

{_join_lines(_signal_lines(context['signals']))}

## Titel

{_join_lines(_unique([*context['report_synthesis']['title_ideas'], *sachbuch['subtitle_ideas']]))}

## Untertitel

{_join_lines(context['report_synthesis']['subtitle_ideas'])}

## Positionierung

{_join_lines(sachbuch['positioning_angles'])}

## Kapitelstruktur

{_join_lines(sachbuch['chapter_blueprint'])}

Synthese:
{context['report_synthesis']['blueprint_summary']}

## Unterkapitel

{_join_lines(sachbuch['subchapter_blueprint'])}

## Praxisbausteine

Praxis-Module:
{_join_lines(sachbuch['practice_modules'])}

Checklisten:
{_join_lines(sachbuch['checklist_ideas'])}

Fallbeispiele:
{_join_lines(sachbuch['case_study_ideas'])}

Glossar:
{_join_lines(sachbuch['glossary_terms'])}

Recherchefragen:
{_join_lines(sachbuch['research_questions'])}

## Produktion

```text
Quellenbedarf:
{_join_lines(sachbuch['source_requirements'])}

Expertenbedarf:
{_join_lines(sachbuch['expert_needs'])}

Cover-Richtung:
{_join_lines(sachbuch['cover_direction'])}

Buchumfang: {sachbuch['target_length']}
Schreibaufwand: {sachbuch['writing_effort']}
```

## Kategorien & Keywords

Kategorien:
{_join_lines(sachbuch['category_strategy'])}

Backend Keywords:
{_join_lines(sachbuch['backend_keywords'])}
"""


def _build_go_no_go_report(context: dict[str, object]) -> str:
    detail = context["cluster_analysis"]
    sachbuch = context["sachbuch_analysis"]
    rationale = (
        sachbuch["sachbuch_score"]["explanation"]
        if sachbuch
        else detail["score"]["explanation"]
    )
    warnings = sachbuch["quality_warnings"] if sachbuch else []
    next_step = (
        "Produktkonzept ausarbeiten und Quellenplan anlegen."
        if context["recommendation"] == "GO"
        else "Weiter beobachten, tiefer pruefen oder nicht priorisieren."
    )
    return f"""# Go / No-Go Report: {detail['main_keyword']}

## Entscheidung

```text
{context['recommendation']}
{rationale}
```

## Warum

```text
{_join_lines(context['competitor_findings'])}
```

## Signal Snapshot

{_join_lines(_signal_lines(context['signals']))}

## Warnhinweise

{_join_lines(_unique([*warnings, context['report_synthesis']['risk_summary']]))}

## Naechster Schritt

```text
{next_step}
```
"""


def _write_report_artifacts(
    *,
    cluster: NicheCluster,
    latest_score: OpportunityScore,
    books: list[Book],
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
    markdown_content: str,
    report_type: str,
    context: dict[str, object],
) -> dict[str, Path | None]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slugify(cluster.name)
    prefix = REPORTS_DIR / f"{slug}_{cluster.id}_{report_type}"

    markdown_path = prefix.with_suffix(".md")
    csv_path = prefix.with_suffix(".csv")
    json_path = prefix.with_suffix(".json")
    pdf_path = prefix.with_suffix(".pdf")

    markdown_path.write_text(markdown_content, encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "asin",
                "title",
                "publisher",
                "price",
                "rating",
                "reviews",
                "latest_bsr",
                "bsr_trend",
                "categories",
                "listing_target_audience",
                "actual_target_audience",
                "ai_target_audience",
                "ai_core_problem",
                "ai_use_case",
                "ai_promised_outcome",
                "listing_quality_score",
                "cover_quality_score",
                "freshness_score",
                "content_depth_score",
                "category_fit_score",
            ]
        )
        for book in cluster_analysis.competitor_books[:25]:
            writer.writerow(
                [
                    book.asin,
                    book.title or "",
                    book.publisher or "",
                    book.latest_price if book.latest_price is not None else "",
                    book.latest_rating if book.latest_rating is not None else "",
                    book.latest_review_count if book.latest_review_count is not None else "",
                    book.bsr.latest_bsr if book.bsr.latest_bsr is not None else "",
                    book.bsr.trend,
                    " | ".join(book.category_labels),
                    book.listing_target_audience or "",
                    book.actual_target_audience or "",
                    book.ai_target_audience or "",
                    book.ai_core_problem or "",
                    book.ai_use_case or "",
                    book.ai_promised_outcome or "",
                    book.listing_quality_score,
                    book.cover_quality_score,
                    book.freshness_score,
                    book.content_depth_score,
                    book.category_fit_score,
                ]
            )

    json_payload = {
        "context": context,
        "report_synthesis": context["report_synthesis"],
        "cluster_analysis": cluster_analysis.model_dump(),
        "sachbuch_analysis": sachbuch_analysis.model_dump() if sachbuch_analysis else None,
        "books": [
            {
                "asin": book.asin,
                "title": book.title,
                "subtitle": book.subtitle,
                "publisher": book.publisher,
                "primary_category": book.primary_category,
                "secondary_category": book.secondary_category,
                "tertiary_category": book.tertiary_category,
                "edition_info": book.edition_info,
                "table_of_contents": book.table_of_contents,
            }
            for book in books[:25]
        ],
        "generic_score": {
            "keyword_specificity_score": latest_score.keyword_specificity_score,
            "new_entrant_signal": latest_score.new_entrant_signal,
            "review_insight_score": latest_score.review_insight_score,
            "demand_score": latest_score.demand_score,
            "saturation_risk": latest_score.saturation_risk,
            "entry_feasibility_score": latest_score.entry_feasibility_score,
            "review_wall_risk": latest_score.review_wall_risk,
            "differentiation_score": latest_score.differentiation_score,
            "ai_slop_score": latest_score.ai_slop_score,
            "brand_dominance_risk": latest_score.brand_dominance_risk,
            "content_complexity_risk": latest_score.content_complexity_risk,
            "compliance_risk": latest_score.compliance_risk,
            "price_compression_risk": latest_score.price_compression_risk,
            "authority_risk": latest_score.authority_risk,
            "research_effort_score": latest_score.research_effort_score,
            "final_score": latest_score.final_score,
            "explanation": latest_score.explanation,
        },
    }
    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    pdf_created = _write_pdf(pdf_path, report_type, context)
    return {
        "markdown": markdown_path,
        "csv": csv_path,
        "json": json_path,
        "pdf": pdf_path if pdf_created else None,
    }


def _write_pdf(pdf_path: Path, report_type: str, context: dict[str, object]) -> bool:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
    except ModuleNotFoundError:
        return False

    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    _, height = A4
    y = height - 2 * cm

    def write_line(text: str, *, size: int = 10, gap: float = 0.5 * cm, bold: bool = False) -> None:
        nonlocal y
        if y < 2 * cm:
            pdf.showPage()
            y = height - 2 * cm
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        for wrapped in wrap(text, width=95):
            pdf.drawString(2 * cm, y, wrapped)
            y -= gap
            if y < 2 * cm:
                pdf.showPage()
                y = height - 2 * cm

    cluster = context["cluster"]
    detail = context["cluster_analysis"]
    sachbuch = context["sachbuch_analysis"]
    write_line(f"{report_type}: {normalize_text(cluster['name']) or cluster['name']}", size=15, bold=True)
    write_line(f"Keyword: {detail['main_keyword']}", bold=True)
    write_line(f"Recommendation: {context['recommendation']}")
    write_line(f"Generic opportunity score: {detail['score']['final_score']}/100")
    write_line(f"Synthesis: {context['report_synthesis']['executive_summary']}")
    write_line("Signal snapshot:", bold=True)
    for line in _signal_lines(context["signals"])[:4]:
        write_line(f"- {line}")
    if sachbuch:
        write_line(f"Sachbuch opportunity score: {sachbuch['sachbuch_score']['final_score']}/100")
    write_line("Top competitor findings:", bold=True)
    for line in context["competitor_findings"]:
        write_line(f"- {line}")
    write_line("Risk highlights:", bold=True)
    for line in context["risk_lines"]:
        write_line(f"- {line}")
    write_line("Keyword strategy:", bold=True)
    for line in detail["keyword_strategy"]["primary_keywords"]:
        write_line(f"- {line}")
    if sachbuch:
        write_line("Blueprint highlights:", bold=True)
        for line in sachbuch["chapter_blueprint"][:5]:
            write_line(f"- {line}")
    pdf.save()
    return True


def _metadata_strategy(
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
) -> list[str]:
    keyword = cluster_analysis.main_keyword
    lines = [
        f"Hauptkeyword '{keyword}' frueh in Titel und Untertitel verankern.",
        "Metadaten auf klaren Nutzen und konkrete Nutzungssituation statt breite Themenwolke ausrichten.",
    ]
    if sachbuch_analysis:
        lines.append(f"Zielgruppe explizit nennen: {sachbuch_analysis.recommended_target_audience}.")
        if sachbuch_analysis.topic_gap.localization_gap_signal and sachbuch_analysis.topic_gap.localization_gap_signal >= 30:
            lines.append("Deutschland-Bezug und lokale Terminologie direkt im Untertitel sichtbar machen.")
    if cluster_analysis.competitor_summary.title_similarity >= 35:
        lines.append("Stark aehnliche Wettbewerbertitel vermeiden und klarer differenzieren.")
    return lines


def _competitor_findings(cluster_analysis: NicheClusterAnalysisRead) -> list[str]:
    summary = cluster_analysis.competitor_summary
    return [
        f"Publisher concentration: {summary.publisher_concentration}",
        f"Title similarity: {summary.title_similarity}",
        f"New entrant visibility: {summary.new_entrant_visibility}",
        f"Average listing quality: {summary.average_listing_quality if summary.average_listing_quality is not None else 'n/a'}",
        f"Average cover quality: {summary.average_cover_quality if summary.average_cover_quality is not None else 'n/a'}",
        f"Category overlap: {summary.category_overlap_score if summary.category_overlap_score is not None else 'n/a'}",
    ]


def _competition_table(competitor_books: list[object]) -> str:
    header = (
        "| Titel | Reviews | BSR | Preis | Formate | Cover | Listing | Publisher | Kategorien |\n"
        "| --- | ---: | ---: | ---: | --- | ---: | ---: | --- | --- |"
    )
    rows = []
    for book in competitor_books:
        rows.append(
            f"| {book.title or book.asin} | {book.latest_review_count if book.latest_review_count is not None else 'n/a'} | "
            f"{book.bsr.latest_bsr if book.bsr.latest_bsr is not None else 'n/a'} | "
            f"{book.latest_price if book.latest_price is not None else 'n/a'} | {book.formats or 'n/a'} | "
            f"{book.cover_quality_score} | {book.listing_quality_score} | {book.publisher or 'n/a'} | "
            f"{', '.join(book.category_labels) if book.category_labels else 'n/a'} |"
        )
    return "\n".join([header, *rows]) if rows else "Keine Wettbewerberdaten verfuegbar."


def _bsr_indicator_lines(competitor_books: list[object]) -> list[str]:
    lines = []
    for book in competitor_books[:5]:
        lines.append(
            f"{book.title or book.asin}: latest BSR {book.bsr.latest_bsr if book.bsr.latest_bsr is not None else 'n/a'}, "
            f"trend {book.bsr.trend}, snapshots {book.bsr.snapshot_count}"
        )
    return lines or ["Keine BSR-Signale sichtbar."]


def _saturation_lines(cluster_analysis: NicheClusterAnalysisRead) -> list[str]:
    summary = cluster_analysis.competitor_summary
    return [
        f"Review Wall: {cluster_analysis.score.review_wall_risk}",
        f"Publisher Dominance: {summary.publisher_concentration}",
        f"Brand Dominance Risk: {cluster_analysis.score.brand_dominance_risk}",
        f"Title Similarity: {summary.title_similarity}",
        f"Price Compression: {cluster_analysis.score.price_compression_risk}",
        f"AI-Slop Density: {cluster_analysis.score.ai_slop_score}",
        f"New Entrant Visibility: {summary.new_entrant_visibility}",
        f"Category Overlap: {summary.category_overlap_score if summary.category_overlap_score is not None else 'n/a'}",
    ]


def _risk_lines(
    cluster_analysis: NicheClusterAnalysisRead,
    sachbuch_analysis: SachbuchAnalysisRead | None,
) -> list[str]:
    lines = [
        f"Keyword Specificity: {cluster_analysis.score.keyword_specificity_score}",
        f"Review Insight Score: {cluster_analysis.score.review_insight_score}",
        f"Authority Risk: {cluster_analysis.score.authority_risk}",
        f"Compliance Risk: {cluster_analysis.score.compliance_risk}",
        f"Content Complexity: {cluster_analysis.score.content_complexity_risk}",
        f"Production Complexity: {cluster_analysis.score.research_effort_score}",
        f"Review Wall Risk: {cluster_analysis.score.review_wall_risk}",
        f"Saturation Risk: {cluster_analysis.score.saturation_risk}",
        f"Copyright Risk: {_copyright_risk_label(cluster_analysis.main_keyword)}",
        f"Trademark Risk: {_trademark_risk_label(cluster_analysis.main_keyword)}",
        f"Medical/Legal/Finance Risk: {_sector_risk_label(cluster_analysis.main_keyword)}",
    ]
    if sachbuch_analysis:
        lines.extend(
            [
                f"Liability Risk: {sachbuch_analysis.sachbuch_score.liability_risk}",
                f"Update Risk: {sachbuch_analysis.sachbuch_score.update_risk}",
                f"Research Effort Risk: {sachbuch_analysis.sachbuch_score.research_effort_risk}",
                f"Publisher Dominance Risk: {sachbuch_analysis.sachbuch_score.publisher_dominance_risk}",
            ]
        )
        lines.extend(sachbuch_analysis.quality_warnings)
    return lines


def _signal_lines(signals: list[dict[str, object]]) -> list[str]:
    lines: list[str] = []
    for signal in signals:
        label = signal.get("label", "Signal")
        direction = signal.get("direction", "neutral")
        score = signal.get("score", "n/a")
        summary = signal.get("summary", "")
        lines.append(f"{label} [{direction}, {score}/100]: {summary}")
    return lines


def _book_structure_section(main_keyword: str, sachbuch: dict[str, object] | None) -> str:
    if sachbuch is None:
        return "\n".join(
            [
                "Titel-Ideen:",
                _join_lines([
                    f"{main_keyword} fuer den Alltag",
                    f"{main_keyword} Arbeitsbuch",
                    f"{main_keyword} kompakt und praktisch",
                ]),
                "",
                "Interior-Struktur:",
                _join_lines(
                    [
                        "Klarer Einstieg, kurze Anleitung, direkt nutzbare Templates.",
                        "Wiederkehrende Tracker, Checklisten oder Uebungen nach Use Case ordnen.",
                        "Bonus-Seiten fuer Zusammenfassung, Fortschritt und persoenliche Notizen einplanen.",
                    ]
                ),
                "",
                "Format:",
                _join_lines(["Praxisnahes Layout mit schneller Orientierung und sauberer Leserfuehrung."]),
            ]
        )
    return "\n".join(
        [
            "Kapitel:",
            _join_lines(sachbuch["chapter_blueprint"]),
            "",
            "Unterkapitel:",
            _join_lines(sachbuch["subchapter_blueprint"]),
            "",
            "Praxisbausteine:",
            _join_lines(sachbuch["practice_modules"]),
            "",
            "Checklisten:",
            _join_lines(sachbuch["checklist_ideas"]),
        ]
    )


def _generic_recommendation(final_score: int) -> str:
    if final_score >= 65:
        return "GO"
    if final_score >= 40:
        return "MAYBE"
    return "NO-GO"


def _copyright_risk_label(keyword: str) -> str:
    lowered = keyword.casefold()
    return "hoch" if "copyright" in lowered or "urheber" in lowered else "niedrig bis mittel"


def _trademark_risk_label(keyword: str) -> str:
    lowered = keyword.casefold()
    return "hoch" if "marke" in lowered or "trademark" in lowered else "niedrig bis mittel"


def _sector_risk_label(keyword: str) -> str:
    lowered = keyword.casefold()
    if any(term in lowered for term in ["medizin", "gesund", "therapie"]):
        return "medizinisch erhoeht"
    if any(term in lowered for term in ["recht", "steuer"]):
        return "rechtlich erhoeht"
    if any(term in lowered for term in ["finanz", "investment"]):
        return "finanziell erhoeht"
    return "niedrig"


def _join_lines(values: object) -> str:
    if isinstance(values, list):
        return "\n".join(f"- {value}" for value in values) or "- n/a"
    return str(values)


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_text(value) or ""
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


def _slugify(text: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "_" for char in text)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "report"
