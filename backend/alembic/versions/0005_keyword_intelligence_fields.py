"""add keyword intelligence metadata fields"""

from alembic import op
import sqlalchemy as sa


revision = "0005_keyword_meta"
down_revision = "0004_score_depth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("keywords", sa.Column("target_audience", sa.String(length=255), nullable=True))
    op.add_column("keywords", sa.Column("category_hint", sa.String(length=255), nullable=True))
    op.add_column("keywords", sa.Column("search_intent_family", sa.String(length=50), nullable=True))
    op.add_column("keywords", sa.Column("audience_clarity_score", sa.Integer(), nullable=True))
    op.add_column("keywords", sa.Column("format_suitability_score", sa.Integer(), nullable=True))
    op.add_column("keywords", sa.Column("competition_probability_score", sa.Integer(), nullable=True))
    op.add_column("keywords", sa.Column("production_effort_score", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("keywords", "production_effort_score")
    op.drop_column("keywords", "competition_probability_score")
    op.drop_column("keywords", "format_suitability_score")
    op.drop_column("keywords", "audience_clarity_score")
    op.drop_column("keywords", "search_intent_family")
    op.drop_column("keywords", "category_hint")
    op.drop_column("keywords", "target_audience")
