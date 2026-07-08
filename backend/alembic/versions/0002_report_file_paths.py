"""add report file path columns"""

from alembic import op
import sqlalchemy as sa


revision = "0002_report_file_paths"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("markdown_path", sa.String(length=1000), nullable=True))
    op.add_column("reports", sa.Column("json_path", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "json_path")
    op.drop_column("reports", "markdown_path")
