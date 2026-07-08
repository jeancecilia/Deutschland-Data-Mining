"""add discovery engine tables"""

from alembic import op
import sqlalchemy as sa


revision = "0006_discovery_engine"
down_revision = "0005_keyword_meta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discovery_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_hint", sa.String(length=255), nullable=True),
        sa.Column("book_type_hint", sa.String(length=50), nullable=True),
        sa.Column("risk_level", sa.String(length=50), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_discovery_topics_slug"), "discovery_topics", ["slug"], unique=False)

    op.create_table(
        "discovery_audiences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_discovery_audiences_slug"), "discovery_audiences", ["slug"], unique=False)

    op.create_table(
        "discovery_pain_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_discovery_pain_points_slug"), "discovery_pain_points", ["slug"], unique=False)

    op.create_table(
        "discovery_contexts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_discovery_contexts_slug"), "discovery_contexts", ["slug"], unique=False)

    op.create_table(
        "discovery_book_formats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("book_type_hint", sa.String(length=50), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_discovery_book_formats_slug"), "discovery_book_formats", ["slug"], unique=False)

    op.create_table(
        "discovery_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("requested_generate_limit", sa.Integer(), nullable=True),
        sa.Column("requested_validate_limit", sa.Integer(), nullable=True),
        sa.Column("generated_count", sa.Integer(), nullable=False),
        sa.Column("validated_count", sa.Integer(), nullable=False),
        sa.Column("kept_count", sa.Integer(), nullable=False),
        sa.Column("auto_generate_reports", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "discovery_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("discovery_run_id", sa.Integer(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("audience_id", sa.Integer(), nullable=True),
        sa.Column("pain_point_id", sa.Integer(), nullable=True),
        sa.Column("context_id", sa.Integer(), nullable=True),
        sa.Column("book_format_id", sa.Integer(), nullable=True),
        sa.Column("candidate_phrase", sa.String(length=255), nullable=False),
        sa.Column("normalized_phrase", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("marketplace", sa.String(length=16), nullable=False),
        sa.Column("book_type_hint", sa.String(length=50), nullable=True),
        sa.Column("validated_book_type", sa.String(length=50), nullable=True),
        sa.Column("risk_level", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("generation_score", sa.Integer(), nullable=True),
        sa.Column("specificity_score", sa.Integer(), nullable=True),
        sa.Column("intent_score", sa.Integer(), nullable=True),
        sa.Column("audience_clarity_score", sa.Integer(), nullable=True),
        sa.Column("format_suitability_score", sa.Integer(), nullable=True),
        sa.Column("competition_probability_score", sa.Integer(), nullable=True),
        sa.Column("production_effort_score", sa.Integer(), nullable=True),
        sa.Column("pain_clarity_score", sa.Integer(), nullable=True),
        sa.Column("keyword_id", sa.Integer(), nullable=True),
        sa.Column("niche_cluster_id", sa.Integer(), nullable=True),
        sa.Column("validated_target_audience", sa.String(length=255), nullable=True),
        sa.Column("demand_score", sa.Integer(), nullable=True),
        sa.Column("competition_score", sa.Integer(), nullable=True),
        sa.Column("gap_score", sa.Integer(), nullable=True),
        sa.Column("production_difficulty_score", sa.Integer(), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("final_opportunity_score", sa.Integer(), nullable=True),
        sa.Column("decision", sa.String(length=50), nullable=True),
        sa.Column("relevant_book_count", sa.Integer(), nullable=True),
        sa.Column("related_keyword_count", sa.Integer(), nullable=True),
        sa.Column("top_competitor_review_median", sa.Integer(), nullable=True),
        sa.Column("bsr_coverage", sa.Integer(), nullable=True),
        sa.Column("report_count", sa.Integer(), nullable=False),
        sa.Column("market_summary", sa.Text(), nullable=True),
        sa.Column("gap_summary", sa.Text(), nullable=True),
        sa.Column("reason_summary", sa.Text(), nullable=True),
        sa.Column("recommended_angle", sa.Text(), nullable=True),
        sa.Column("validation_notes", sa.Text(), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["audience_id"], ["discovery_audiences.id"]),
        sa.ForeignKeyConstraint(["book_format_id"], ["discovery_book_formats.id"]),
        sa.ForeignKeyConstraint(["context_id"], ["discovery_contexts.id"]),
        sa.ForeignKeyConstraint(["discovery_run_id"], ["discovery_runs.id"]),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywords.id"]),
        sa.ForeignKeyConstraint(["niche_cluster_id"], ["niche_clusters.id"]),
        sa.ForeignKeyConstraint(["pain_point_id"], ["discovery_pain_points.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["discovery_topics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_phrase"),
    )
    op.create_index(op.f("ix_discovery_candidates_discovery_run_id"), "discovery_candidates", ["discovery_run_id"], unique=False)
    op.create_index(op.f("ix_discovery_candidates_topic_id"), "discovery_candidates", ["topic_id"], unique=False)
    op.create_index(op.f("ix_discovery_candidates_audience_id"), "discovery_candidates", ["audience_id"], unique=False)
    op.create_index(op.f("ix_discovery_candidates_pain_point_id"), "discovery_candidates", ["pain_point_id"], unique=False)
    op.create_index(op.f("ix_discovery_candidates_context_id"), "discovery_candidates", ["context_id"], unique=False)
    op.create_index(op.f("ix_discovery_candidates_book_format_id"), "discovery_candidates", ["book_format_id"], unique=False)
    op.create_index(op.f("ix_discovery_candidates_candidate_phrase"), "discovery_candidates", ["candidate_phrase"], unique=False)
    op.create_index(op.f("ix_discovery_candidates_normalized_phrase"), "discovery_candidates", ["normalized_phrase"], unique=False)
    op.create_index(op.f("ix_discovery_candidates_keyword_id"), "discovery_candidates", ["keyword_id"], unique=False)
    op.create_index(op.f("ix_discovery_candidates_niche_cluster_id"), "discovery_candidates", ["niche_cluster_id"], unique=False)

    discovery_topics = sa.table(
        "discovery_topics",
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("category_hint", sa.String()),
        sa.column("book_type_hint", sa.String()),
        sa.column("risk_level", sa.String()),
        sa.column("priority", sa.Integer()),
        sa.column("active", sa.Boolean()),
    )
    discovery_audiences = sa.table(
        "discovery_audiences",
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("priority", sa.Integer()),
        sa.column("active", sa.Boolean()),
    )
    discovery_pain_points = sa.table(
        "discovery_pain_points",
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("priority", sa.Integer()),
        sa.column("active", sa.Boolean()),
    )
    discovery_contexts = sa.table(
        "discovery_contexts",
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("priority", sa.Integer()),
        sa.column("active", sa.Boolean()),
    )
    discovery_book_formats = sa.table(
        "discovery_book_formats",
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("book_type_hint", sa.String()),
        sa.column("priority", sa.Integer()),
        sa.column("active", sa.Boolean()),
    )

    op.bulk_insert(
        discovery_topics,
        [
            {"name": "Pflege", "slug": "pflege", "description": "Pflegeorganisation, Dokumentation und Familienalltag.", "category_hint": "Gesundheit und Dokumentation", "book_type_hint": "sachbuch", "risk_level": "medium", "priority": 96, "active": True},
            {"name": "Blutdruck", "slug": "blutdruck", "description": "Selbstbeobachtung und Alltagstracking.", "category_hint": "Gesundheit und Dokumentation", "book_type_hint": "medium_content", "risk_level": "medium", "priority": 93, "active": True},
            {"name": "Blutzucker", "slug": "blutzucker", "description": "Messroutinen, Dokumentation und Verlauf.", "category_hint": "Gesundheit und Dokumentation", "book_type_hint": "medium_content", "risk_level": "medium", "priority": 88, "active": True},
            {"name": "ADHS", "slug": "adhs", "description": "Struktur, Alltagsorganisation und Selbstmanagement.", "category_hint": "Selbsthilfe und mentale Gesundheit", "book_type_hint": "sachbuch", "risk_level": "medium", "priority": 94, "active": True},
            {"name": "Haushalt", "slug": "haushalt", "description": "Alltagsorganisation, Listen und Routinen.", "category_hint": "Familie und Alltag", "book_type_hint": "medium_content", "risk_level": "low", "priority": 82, "active": True},
            {"name": "Pflegegrad-Antrag", "slug": "pflegegrad-antrag", "description": "Antraege, Unterlagen und Behordengaenge.", "category_hint": "Gesundheit und Dokumentation", "book_type_hint": "sachbuch", "risk_level": "medium", "priority": 91, "active": True},
            {"name": "Hundegesundheit", "slug": "hundegesundheit", "description": "Symptombeobachtung und Tieralltag.", "category_hint": "Hobby und Freizeit", "book_type_hint": "medium_content", "risk_level": "low", "priority": 80, "active": True},
            {"name": "Schichtarbeit", "slug": "schichtarbeit", "description": "Rhythmus, Routinen und Belastungssteuerung.", "category_hint": "Beruf und Business", "book_type_hint": "medium_content", "risk_level": "low", "priority": 78, "active": True},
            {"name": "Nebengewerbe", "slug": "nebengewerbe", "description": "Einstieg, Struktur und Kleinunternehmeralltag.", "category_hint": "Beruf und Business", "book_type_hint": "sachbuch", "risk_level": "medium", "priority": 84, "active": True},
            {"name": "KI im Handwerk", "slug": "ki-im-handwerk", "description": "Praktische KI-Anwendung fuer kleine Betriebe.", "category_hint": "Beruf und Business", "book_type_hint": "sachbuch", "risk_level": "medium", "priority": 86, "active": True},
            {"name": "Behordenpost", "slug": "behoerdenpost", "description": "Briefe, Fristen und private Ordnung.", "category_hint": "Familie und Alltag", "book_type_hint": "medium_content", "risk_level": "low", "priority": 76, "active": True},
            {"name": "Trauer", "slug": "trauer", "description": "Selbsthilfe, Begleitung und Orientierung.", "category_hint": "Selbsthilfe und mentale Gesundheit", "book_type_hint": "sachbuch", "risk_level": "medium", "priority": 73, "active": True},
            {"name": "Lernorganisation", "slug": "lernorganisation", "description": "Pruefungsvorbereitung, Fokus und Lernplanung.", "category_hint": "Lernen und Bildung", "book_type_hint": "medium_content", "risk_level": "low", "priority": 81, "active": True},
        ],
    )
    op.bulk_insert(
        discovery_audiences,
        [
            {"name": "Senioren", "slug": "senioren", "description": "Aeltere Leser mit klarer Alltagssituation.", "priority": 90, "active": True},
            {"name": "Angehoerige", "slug": "angehoerige", "description": "Familienmitglieder mit Betreuungs- und Organisationsbedarf.", "priority": 96, "active": True},
            {"name": "Eltern", "slug": "eltern", "description": "Eltern mit Organisations- oder Begleitaufgaben.", "priority": 86, "active": True},
            {"name": "Selbststaendige", "slug": "selbststaendige", "description": "Solo-Selbststaendige mit Zeitdruck und Strukturbedarf.", "priority": 84, "active": True},
            {"name": "Handwerker", "slug": "handwerker", "description": "Kleine Betriebe und operative Teams.", "priority": 83, "active": True},
            {"name": "Lehrer", "slug": "lehrer", "description": "Berufsalltag mit hoher Planungsdichte.", "priority": 72, "active": True},
            {"name": "Hundehalter", "slug": "hundehalter", "description": "Tierhalter mit Beobachtungs- und Routinenthemen.", "priority": 78, "active": True},
            {"name": "Studierende", "slug": "studierende", "description": "Junge Erwachsene mit Lern- und Organisationsbedarf.", "priority": 74, "active": True},
            {"name": "Erwachsene mit ADHS", "slug": "erwachsene-mit-adhs", "description": "Klare Zielgruppe fuer Struktur- und Routinenangebote.", "priority": 92, "active": True},
            {"name": "Alleinerziehende", "slug": "alleinerziehende", "description": "Haushalts- und Familienorganisation unter Zeitdruck.", "priority": 79, "active": True},
            {"name": "Schichtarbeiter", "slug": "schichtarbeiter", "description": "Berufsalltag mit wechselnden Routinen.", "priority": 71, "active": True},
        ],
    )
    op.bulk_insert(
        discovery_pain_points,
        [
            {"name": "Dokumentation", "slug": "dokumentation", "description": "Informationen sauber festhalten.", "priority": 94, "active": True},
            {"name": "Ueberforderung", "slug": "ueberforderung", "description": "Zu viel Komplexitaet ohne klare Struktur.", "priority": 89, "active": True},
            {"name": "Zeitmangel", "slug": "zeitmangel", "description": "Wenig Zeit fuer Recherche und Umsetzung.", "priority": 88, "active": True},
            {"name": "Angst vor Fehlern", "slug": "angst-vor-fehlern", "description": "Hoher Druck, nichts falsch zu machen.", "priority": 87, "active": True},
            {"name": "fehlende Struktur", "slug": "fehlende-struktur", "description": "Ablauf und Reihenfolge sind unklar.", "priority": 91, "active": True},
            {"name": "Buerokratie", "slug": "buerokratie", "description": "Antraege, Nachweise und Verwaltungslast.", "priority": 86, "active": True},
            {"name": "Alltag organisieren", "slug": "alltag-organisieren", "description": "Wiederkehrende Routinen greifbar machen.", "priority": 84, "active": True},
            {"name": "Symptome beobachten", "slug": "symptome-beobachten", "description": "Verlaeufe und Hinweise systematisch tracken.", "priority": 82, "active": True},
            {"name": "Routinen aufbauen", "slug": "routinen-aufbauen", "description": "Verhalten sauber einueben und halten.", "priority": 80, "active": True},
        ],
    )
    op.bulk_insert(
        discovery_contexts,
        [
            {"name": "nach Krankenhausentlassung", "slug": "nach-krankenhausentlassung", "description": "Hoher Informations- und Strukturbedarf nach Entlassung.", "priority": 95, "active": True},
            {"name": "im Alltag", "slug": "im-alltag", "description": "Alltaeglicher Einsatz mit wenig Reibung.", "priority": 84, "active": True},
            {"name": "fuer Einsteiger", "slug": "fuer-einsteiger", "description": "No-Vorwissen, niedrige Einstiegshuerde.", "priority": 86, "active": True},
            {"name": "im Familienalltag", "slug": "im-familienalltag", "description": "Mehrere Rollen und wenig Zeit.", "priority": 82, "active": True},
            {"name": "im Berufsalltag", "slug": "im-berufsalltag", "description": "Praxisnahe Anwendung waehrend der Arbeit.", "priority": 80, "active": True},
            {"name": "bei Behoerden", "slug": "bei-behoerden", "description": "Formulare, Fristen und Nachweise.", "priority": 88, "active": True},
            {"name": "fuer Zuhause", "slug": "fuer-zuhause", "description": "Nutzung ohne professionelle Umgebung.", "priority": 74, "active": True},
            {"name": "waehrend Schichtarbeit", "slug": "waehrend-schichtarbeit", "description": "Wechselnde Routinen und begrenzte Energie.", "priority": 70, "active": True},
            {"name": "vor dem Pflegegrad-Antrag", "slug": "vor-dem-pflegegrad-antrag", "description": "Vorbereitung auf Dokumentation und Antragstellung.", "priority": 90, "active": True},
            {"name": "mit wenig Zeit", "slug": "mit-wenig-zeit", "description": "Schnelle Nutzbarkeit ohne Theorieballast.", "priority": 79, "active": True},
        ],
    )
    op.bulk_insert(
        discovery_book_formats,
        [
            {"name": "Tagebuch", "slug": "tagebuch", "description": "Fortlaufende Selbstbeobachtung und Eintragungen.", "book_type_hint": "medium_content", "priority": 90, "active": True},
            {"name": "Planer", "slug": "planer", "description": "Struktur und Terminlogik.", "book_type_hint": "medium_content", "priority": 88, "active": True},
            {"name": "Arbeitsbuch", "slug": "arbeitsbuch", "description": "Umsetzungsorientierte Aufgaben und Uebungen.", "book_type_hint": "medium_content", "priority": 82, "active": True},
            {"name": "Checklistenbuch", "slug": "checklistenbuch", "description": "Schnell nutzbare Schrittfolgen und Vorlagen.", "book_type_hint": "medium_content", "priority": 96, "active": True},
            {"name": "Leitfaden", "slug": "leitfaden", "description": "Praxisratgeber mit klarer Orientierung.", "book_type_hint": "sachbuch", "priority": 87, "active": True},
            {"name": "Vorlagenbuch", "slug": "vorlagenbuch", "description": "Sammlung direkt nutzbarer Vorlagen.", "book_type_hint": "medium_content", "priority": 85, "active": True},
            {"name": "Workbook", "slug": "workbook", "description": "Angeleitete Umsetzung mit Reflexionsanteil.", "book_type_hint": "sachbuch", "priority": 78, "active": True},
            {"name": "Tracker", "slug": "tracker", "description": "Mess- und Fortschrittsverfolgung.", "book_type_hint": "medium_content", "priority": 84, "active": True},
            {"name": "Ordner", "slug": "ordner", "description": "Dokumenten- und Uebersichtsstruktur.", "book_type_hint": "medium_content", "priority": 91, "active": True},
            {"name": "Praxisbuch", "slug": "praxisbuch", "description": "Mehr Tiefe als ein Template, aber klar an der Anwendung.", "book_type_hint": "sachbuch", "priority": 80, "active": True},
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_discovery_candidates_niche_cluster_id"), table_name="discovery_candidates")
    op.drop_index(op.f("ix_discovery_candidates_keyword_id"), table_name="discovery_candidates")
    op.drop_index(op.f("ix_discovery_candidates_normalized_phrase"), table_name="discovery_candidates")
    op.drop_index(op.f("ix_discovery_candidates_candidate_phrase"), table_name="discovery_candidates")
    op.drop_index(op.f("ix_discovery_candidates_book_format_id"), table_name="discovery_candidates")
    op.drop_index(op.f("ix_discovery_candidates_context_id"), table_name="discovery_candidates")
    op.drop_index(op.f("ix_discovery_candidates_pain_point_id"), table_name="discovery_candidates")
    op.drop_index(op.f("ix_discovery_candidates_audience_id"), table_name="discovery_candidates")
    op.drop_index(op.f("ix_discovery_candidates_topic_id"), table_name="discovery_candidates")
    op.drop_index(op.f("ix_discovery_candidates_discovery_run_id"), table_name="discovery_candidates")
    op.drop_table("discovery_candidates")
    op.drop_table("discovery_runs")
    op.drop_index(op.f("ix_discovery_book_formats_slug"), table_name="discovery_book_formats")
    op.drop_table("discovery_book_formats")
    op.drop_index(op.f("ix_discovery_contexts_slug"), table_name="discovery_contexts")
    op.drop_table("discovery_contexts")
    op.drop_index(op.f("ix_discovery_pain_points_slug"), table_name="discovery_pain_points")
    op.drop_table("discovery_pain_points")
    op.drop_index(op.f("ix_discovery_audiences_slug"), table_name="discovery_audiences")
    op.drop_table("discovery_audiences")
    op.drop_index(op.f("ix_discovery_topics_slug"), table_name="discovery_topics")
    op.drop_table("discovery_topics")
