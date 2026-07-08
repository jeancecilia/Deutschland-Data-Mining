"""add quality hardening fields to niche_candidates

Adds: risk_category, risk_reason_codes, manual_review_required,
      authority_required, disclaimer_required, auto_promote_allowed,
      compatibility_score, suggested_rewrites
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "0009_discovery_quality"
down_revision = "0008_discovery_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("niche_candidates", sa.Column("risk_category", sa.String(length=50), nullable=True,
                                                  comment="low, medium, high, restricted, blocked"))
    op.add_column("niche_candidates", sa.Column("risk_reason_codes", JSONB(), nullable=True))
    op.add_column("niche_candidates", sa.Column("manual_review_required", sa.Boolean(), nullable=False,
                                                  server_default=sa.text("false")))
    op.add_column("niche_candidates", sa.Column("authority_required", sa.Boolean(), nullable=False,
                                                  server_default=sa.text("false")))
    op.add_column("niche_candidates", sa.Column("disclaimer_required", sa.Boolean(), nullable=False,
                                                  server_default=sa.text("false")))
    op.add_column("niche_candidates", sa.Column("auto_promote_allowed", sa.Boolean(), nullable=False,
                                                  server_default=sa.text("true")))
    op.add_column("niche_candidates", sa.Column("compatibility_score", sa.Integer(), nullable=True))
    op.add_column("niche_candidates", sa.Column("suggested_rewrites", JSONB(), nullable=True))
    op.add_column("niche_candidates", sa.Column("recommendation_label", sa.String(length=50), nullable=True,
                                                  comment="GO, MAYBE, NO-GO, REVIEW_REQUIRED, HIGH_RISK_OPPORTUNITY, BLOCKED"))


def downgrade() -> None:
    op.drop_column("niche_candidates", "recommendation_label")
    op.drop_column("niche_candidates", "suggested_rewrites")
    op.drop_column("niche_candidates", "compatibility_score")
    op.drop_column("niche_candidates", "auto_promote_allowed")
    op.drop_column("niche_candidates", "disclaimer_required")
    op.drop_column("niche_candidates", "authority_required")
    op.drop_column("niche_candidates", "manual_review_required")
    op.drop_column("niche_candidates", "risk_reason_codes")
    op.drop_column("niche_candidates", "risk_category")
