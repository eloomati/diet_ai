"""create email_logs table

Revision ID: 20260718_04_email_logs
Revises: 20260718_03_email_verification
Create Date: 2026-07-18 10:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260718_04_email_logs"
down_revision: Union[str, Sequence[str], None] = "20260718_03_email_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        # No FK to users — a log entry must survive even if the user record
        # is later deleted.
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_logs_to", "email_logs", ["to"], unique=False)
    op.create_index("ix_email_logs_purpose", "email_logs", ["purpose"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_email_logs_purpose", table_name="email_logs")
    op.drop_index("ix_email_logs_to", table_name="email_logs")
    op.drop_table("email_logs")
