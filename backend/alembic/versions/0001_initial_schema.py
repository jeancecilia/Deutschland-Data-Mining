"""initial schema"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asin", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("subtitle", sa.String(length=500), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("marketplace", sa.String(length=16), nullable=False),
        sa.Column("formats", sa.String(length=255), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.String(length=1000), nullable=True),
        sa.Column("book_class", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asin"),
    )
    op.create_index(op.f("ix_books_asin"), "books", ["asin"], unique=False)

    op.create_table(
        "keywords",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("keyword", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("marketplace", sa.String(length=16), nullable=False),
        sa.Column("seed_keyword_id", sa.Integer(), nullable=True),
        sa.Column("keyword_type", sa.String(length=50), nullable=True),
        sa.Column("specificity_score", sa.Integer(), nullable=True),
        sa.Column("intent_score", sa.Integer(), nullable=True),
        sa.Column("book_type", sa.String(length=50), nullable=True),
        sa.Column("risk_level", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["seed_keyword_id"], ["keywords.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_keywords_keyword"), "keywords", ["keyword"], unique=False)

    op.create_table(
        "niche_clusters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("marketplace", sa.String(length=16), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("main_keyword", sa.String(length=255), nullable=True),
        sa.Column("book_class", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("verified_purchase", sa.Boolean(), nullable=True),
        sa.Column("helpful_count", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reviews_book_id"), "reviews", ["book_id"], unique=False)

    op.create_table(
        "review_clusters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("cluster_name", sa.String(length=255), nullable=False),
        sa.Column("sentiment", sa.String(length=50), nullable=False),
        sa.Column("frequency", sa.Integer(), nullable=True),
        sa.Column("severity", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("example_snippets", sa.Text(), nullable=True),
        sa.Column("suggested_improvements", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_review_clusters_book_id"), "review_clusters", ["book_id"], unique=False)

    op.create_table(
        "search_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("keyword_id", sa.Integer(), nullable=False),
        sa.Column("marketplace", sa.String(length=16), nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywords.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_search_runs_keyword_id"), "search_runs", ["keyword_id"], unique=False)

    op.create_table(
        "bsr_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("marketplace", sa.String(length=16), nullable=False),
        sa.Column("bsr_main", sa.Integer(), nullable=True),
        sa.Column("category_bsr_1", sa.Integer(), nullable=True),
        sa.Column("category_bsr_2", sa.Integer(), nullable=True),
        sa.Column("category_bsr_3", sa.Integer(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bsr_snapshots_book_id"), "bsr_snapshots", ["book_id"], unique=False)

    op.create_table(
        "niche_cluster_books",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("niche_cluster_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("relevance_score", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.ForeignKeyConstraint(["niche_cluster_id"], ["niche_clusters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_niche_cluster_books_book_id"), "niche_cluster_books", ["book_id"], unique=False
    )
    op.create_index(
        op.f("ix_niche_cluster_books_niche_cluster_id"),
        "niche_cluster_books",
        ["niche_cluster_id"],
        unique=False,
    )

    op.create_table(
        "niche_cluster_keywords",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("niche_cluster_id", sa.Integer(), nullable=False),
        sa.Column("keyword_id", sa.Integer(), nullable=False),
        sa.Column("relevance_score", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywords.id"]),
        sa.ForeignKeyConstraint(["niche_cluster_id"], ["niche_clusters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_niche_cluster_keywords_keyword_id"),
        "niche_cluster_keywords",
        ["keyword_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_niche_cluster_keywords_niche_cluster_id"),
        "niche_cluster_keywords",
        ["niche_cluster_id"],
        unique=False,
    )

    op.create_table(
        "opportunity_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("niche_cluster_id", sa.Integer(), nullable=False),
        sa.Column("demand_score", sa.Integer(), nullable=True),
        sa.Column("saturation_risk", sa.Integer(), nullable=True),
        sa.Column("entry_feasibility_score", sa.Integer(), nullable=True),
        sa.Column("review_wall_risk", sa.Integer(), nullable=True),
        sa.Column("differentiation_score", sa.Integer(), nullable=True),
        sa.Column("ai_slop_score", sa.Integer(), nullable=True),
        sa.Column("content_complexity_risk", sa.Integer(), nullable=True),
        sa.Column("price_compression_risk", sa.Integer(), nullable=True),
        sa.Column("authority_risk", sa.Integer(), nullable=True),
        sa.Column("research_effort_score", sa.Integer(), nullable=True),
        sa.Column("final_score", sa.Integer(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["niche_cluster_id"], ["niche_clusters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_opportunity_scores_niche_cluster_id"),
        "opportunity_scores",
        ["niche_cluster_id"],
        unique=False,
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("niche_cluster_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("markdown_content", sa.Text(), nullable=True),
        sa.Column("pdf_path", sa.String(length=1000), nullable=True),
        sa.Column("csv_path", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["niche_cluster_id"], ["niche_clusters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_niche_cluster_id"), "reports", ["niche_cluster_id"], unique=False)

    op.create_table(
        "sachbuch_topic_gaps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("niche_cluster_id", sa.Integer(), nullable=False),
        sa.Column("topic_gap_summary", sa.Text(), nullable=True),
        sa.Column("outdated_content_signal", sa.Integer(), nullable=True),
        sa.Column("missing_examples_signal", sa.Integer(), nullable=True),
        sa.Column("missing_checklists_signal", sa.Integer(), nullable=True),
        sa.Column("localization_gap_signal", sa.Integer(), nullable=True),
        sa.Column("content_depth_score", sa.Integer(), nullable=True),
        sa.Column("authority_required", sa.Boolean(), nullable=False),
        sa.Column("expert_review_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["niche_cluster_id"], ["niche_clusters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sachbuch_topic_gaps_niche_cluster_id"),
        "sachbuch_topic_gaps",
        ["niche_cluster_id"],
        unique=False,
    )

    op.create_table(
        "search_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("search_run_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_sponsored", sa.Boolean(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.ForeignKeyConstraint(["search_run_id"], ["search_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_search_results_book_id"), "search_results", ["book_id"], unique=False)
    op.create_index(
        op.f("ix_search_results_search_run_id"), "search_results", ["search_run_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_search_results_search_run_id"), table_name="search_results")
    op.drop_index(op.f("ix_search_results_book_id"), table_name="search_results")
    op.drop_table("search_results")
    op.drop_index(op.f("ix_sachbuch_topic_gaps_niche_cluster_id"), table_name="sachbuch_topic_gaps")
    op.drop_table("sachbuch_topic_gaps")
    op.drop_index(op.f("ix_reports_niche_cluster_id"), table_name="reports")
    op.drop_table("reports")
    op.drop_index(op.f("ix_opportunity_scores_niche_cluster_id"), table_name="opportunity_scores")
    op.drop_table("opportunity_scores")
    op.drop_index(op.f("ix_niche_cluster_keywords_niche_cluster_id"), table_name="niche_cluster_keywords")
    op.drop_index(op.f("ix_niche_cluster_keywords_keyword_id"), table_name="niche_cluster_keywords")
    op.drop_table("niche_cluster_keywords")
    op.drop_index(op.f("ix_niche_cluster_books_niche_cluster_id"), table_name="niche_cluster_books")
    op.drop_index(op.f("ix_niche_cluster_books_book_id"), table_name="niche_cluster_books")
    op.drop_table("niche_cluster_books")
    op.drop_index(op.f("ix_bsr_snapshots_book_id"), table_name="bsr_snapshots")
    op.drop_table("bsr_snapshots")
    op.drop_index(op.f("ix_search_runs_keyword_id"), table_name="search_runs")
    op.drop_table("search_runs")
    op.drop_index(op.f("ix_review_clusters_book_id"), table_name="review_clusters")
    op.drop_table("review_clusters")
    op.drop_index(op.f("ix_reviews_book_id"), table_name="reviews")
    op.drop_table("reviews")
    op.drop_table("niche_clusters")
    op.drop_index(op.f("ix_keywords_keyword"), table_name="keywords")
    op.drop_table("keywords")
    op.drop_index(op.f("ix_books_asin"), table_name="books")
    op.drop_table("books")
