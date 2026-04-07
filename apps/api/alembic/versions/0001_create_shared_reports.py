"""create shared_reports table

Revision ID: 0001
Revises:
Create Date: 2026-04-07 00:00:00.000000
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shared_reports",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("report", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_shared_reports_expires", "shared_reports", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_shared_reports_expires", table_name="shared_reports")
    op.drop_table("shared_reports")
