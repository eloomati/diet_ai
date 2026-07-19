"""add photos column to dietitian_profiles

Revision ID: 20260719_08_dietitian_photos
Revises: 20260719_07_dietitian_tables
Create Date: 2026-07-19 15:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260719_08_dietitian_photos"
down_revision: Union[str, Sequence[str], None] = "20260719_07_dietitian_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "dietitian_profiles",
        sa.Column(
            "photos",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("dietitian_profiles", "photos")
