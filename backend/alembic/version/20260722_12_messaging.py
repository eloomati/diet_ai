"""create dietitian_threads and dietitian_messages tables

Revision ID: 20260722_12_messaging
Revises: 20260722_11_notifications
Create Date: 2026-07-22 11:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260722_12_messaging"
down_revision: Union[str, Sequence[str], None] = "20260722_11_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dietitian_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dietitian_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dietitian_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dietitian_threads_participants",
        "dietitian_threads",
        ["user_id", "dietitian_id"],
        unique=True,
    )

    op.create_table(
        "dietitian_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("diet_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["thread_id"], ["dietitian_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dietitian_messages_thread_id",
        "dietitian_messages",
        ["thread_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_dietitian_messages_thread_id", table_name="dietitian_messages")
    op.drop_table("dietitian_messages")

    op.drop_index("ix_dietitian_threads_participants", table_name="dietitian_threads")
    op.drop_table("dietitian_threads")
