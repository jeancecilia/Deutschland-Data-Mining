"""add keyword priority and deeper opportunity score fields"""

from alembic import op
import sqlalchemy as sa


revision = "0004_score_depth"
down_revision = "0003_sachbuch_depth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("keywords", sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.alter_column("keywords", "priority", server_default=None)

    op.add_column("opportunity_scores", sa.Column("keyword_specificity_score", sa.Integer(), nullable=True))
    op.add_column("opportunity_scores", sa.Column("new_entrant_signal", sa.Integer(), nullable=True))
    op.add_column("opportunity_scores", sa.Column("review_insight_score", sa.Integer(), nullable=True))
    op.add_column("opportunity_scores", sa.Column("brand_dominance_risk", sa.Integer(), nullable=True))
    op.add_column("opportunity_scores", sa.Column("compliance_risk", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("opportunity_scores", "compliance_risk")
    op.drop_column("opportunity_scores", "brand_dominance_risk")
    op.drop_column("opportunity_scores", "review_insight_score")
    op.drop_column("opportunity_scores", "new_entrant_signal")
    op.drop_column("opportunity_scores", "keyword_specificity_score")
    op.drop_column("keywords", "priority")
