"""add retry tracking columns to email_logs

Revision ID: 20260718_05_email_retry
Revises: 20260718_04_email_logs
Create Date: 2026-07-18 11:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260718_05_email_retry"
down_revision: Union[str, Sequence[str], None] = "20260718_04_email_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "email_logs",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "email_logs",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("email_logs", "next_retry_at")
    op.drop_column("email_logs", "attempts")
