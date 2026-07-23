"""add role column to users

Revision ID: 20260719_06_user_roles
Revises: 20260718_05_email_retry
Create Date: 2026-07-19 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260719_06_user_roles"
down_revision: Union[str, Sequence[str], None] = "20260718_05_email_retry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=32), nullable=False, server_default=sa.text("'USER'")),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
