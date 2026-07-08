"""add ai semantic intelligence tables and fields"""

from alembic import op
import sqlalchemy as sa


revision = "0007_ai_semantic"
down_revision = "0006_discovery_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "book_insights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("semantic_key", sa.String(length=255), nullable=True),
        sa.Column("semantic_summary", sa.Text(), nullable=True),
        sa.Column("target_audience", sa.String(length=255), nullable=True),
        sa.Column("core_problem", sa.String(length=255), nullable=True),
        sa.Column("use_case", sa.String(length=255), nullable=True),
        sa.Column("promised_outcome", sa.String(length=255), nullable=True),
        sa.Column("book_format", sa.String(length=100), nullable=True),
        sa.Column("feature_terms", sa.JSON(), nullable=True),
        sa.Column("category_terms", sa.JSON(), nullable=True),
        sa.Column("quality_flags", sa.JSON(), nullable=True),
        sa.Column("localization_notes", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id"),
    )
    op.create_index(op.f("ix_book_insights_book_id"), "book_insights", ["book_id"], unique=False)
    op.create_index(op.f("ix_book_insights_semantic_key"), "book_insights", ["semantic_key"], unique=False)

    op.add_column("review_clusters", sa.Column("cluster_type", sa.String(length=50), nullable=True))
    op.add_column("review_clusters", sa.Column("theme_key", sa.String(length=100), nullable=True))
    op.add_column("review_clusters", sa.Column("semantic_key", sa.String(length=255), nullable=True))
    op.add_column("review_clusters", sa.Column("source_method", sa.String(length=50), nullable=True))
    op.add_column("review_clusters", sa.Column("confidence_score", sa.Integer(), nullable=True))
    op.add_column("review_clusters", sa.Column("buyer_words", sa.JSON(), nullable=True))
    op.add_column("review_clusters", sa.Column("audience_hint", sa.String(length=255), nullable=True))
    op.add_column("review_clusters", sa.Column("missing_feature", sa.String(length=255), nullable=True))
    op.add_column("review_clusters", sa.Column("evidence_terms", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_review_clusters_semantic_key"), "review_clusters", ["semantic_key"], unique=False)

    op.add_column("discovery_candidates", sa.Column("semantic_key", sa.String(length=255), nullable=True))
    op.add_column("discovery_candidates", sa.Column("semantic_family", sa.String(length=255), nullable=True))
    op.create_index(
        op.f("ix_discovery_candidates_semantic_key"),
        "discovery_candidates",
        ["semantic_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_discovery_candidates_semantic_key"), table_name="discovery_candidates")
    op.drop_column("discovery_candidates", "semantic_family")
    op.drop_column("discovery_candidates", "semantic_key")

    op.drop_index(op.f("ix_review_clusters_semantic_key"), table_name="review_clusters")
    op.drop_column("review_clusters", "evidence_terms")
    op.drop_column("review_clusters", "missing_feature")
    op.drop_column("review_clusters", "audience_hint")
    op.drop_column("review_clusters", "buyer_words")
    op.drop_column("review_clusters", "confidence_score")
    op.drop_column("review_clusters", "source_method")
    op.drop_column("review_clusters", "semantic_key")
    op.drop_column("review_clusters", "theme_key")
    op.drop_column("review_clusters", "cluster_type")

    op.drop_index(op.f("ix_book_insights_semantic_key"), table_name="book_insights")
    op.drop_index(op.f("ix_book_insights_book_id"), table_name="book_insights")
    op.drop_table("book_insights")
