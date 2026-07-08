"""add sachbuch opportunity scores and richer book metadata"""

from alembic import op
import sqlalchemy as sa


revision = "0003_sachbuch_depth"
down_revision = "0002_report_file_paths"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("books", sa.Column("edition_info", sa.String(length=255), nullable=True))
    op.add_column("books", sa.Column("primary_category", sa.String(length=255), nullable=True))
    op.add_column("books", sa.Column("secondary_category", sa.String(length=255), nullable=True))
    op.add_column("books", sa.Column("tertiary_category", sa.String(length=255), nullable=True))
    op.add_column("books", sa.Column("table_of_contents", sa.Text(), nullable=True))

    op.create_table(
        "sachbuch_opportunity_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("niche_cluster_id", sa.Integer(), nullable=False),
        sa.Column("german_demand_signal", sa.Integer(), nullable=True),
        sa.Column("topic_gap_signal", sa.Integer(), nullable=True),
        sa.Column("depth_weakness_signal", sa.Integer(), nullable=True),
        sa.Column("freshness_need_signal", sa.Integer(), nullable=True),
        sa.Column("localization_signal", sa.Integer(), nullable=True),
        sa.Column("differentiation_signal", sa.Integer(), nullable=True),
        sa.Column("evergreen_potential_signal", sa.Integer(), nullable=True),
        sa.Column("monetization_potential_signal", sa.Integer(), nullable=True),
        sa.Column("authority_risk", sa.Integer(), nullable=True),
        sa.Column("research_effort_risk", sa.Integer(), nullable=True),
        sa.Column("liability_risk", sa.Integer(), nullable=True),
        sa.Column("update_risk", sa.Integer(), nullable=True),
        sa.Column("publisher_dominance_risk", sa.Integer(), nullable=True),
        sa.Column("review_wall_risk", sa.Integer(), nullable=True),
        sa.Column("final_score", sa.Integer(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["niche_cluster_id"], ["niche_clusters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sachbuch_opportunity_scores_niche_cluster_id"),
        "sachbuch_opportunity_scores",
        ["niche_cluster_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_sachbuch_opportunity_scores_niche_cluster_id"),
        table_name="sachbuch_opportunity_scores",
    )
    op.drop_table("sachbuch_opportunity_scores")
    op.drop_column("books", "table_of_contents")
    op.drop_column("books", "tertiary_category")
    op.drop_column("books", "secondary_category")
    op.drop_column("books", "primary_category")
    op.drop_column("books", "edition_info")
