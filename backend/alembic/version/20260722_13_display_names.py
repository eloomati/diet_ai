"""add display_name to users and first_name/last_name to dietitian_profiles

Revision ID: 20260722_13_display_names
Revises: 20260722_12_messaging
Create Date: 2026-07-22 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260722_13_display_names"
down_revision: Union[str, Sequence[str], None] = "20260722_12_messaging"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=50), nullable=True))
    op.add_column(
        "dietitian_profiles", sa.Column("first_name", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "dietitian_profiles", sa.Column("last_name", sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("dietitian_profiles", "last_name")
    op.drop_column("dietitian_profiles", "first_name")
    op.drop_column("users", "display_name")
