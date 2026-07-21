"""create reviews table

Revision ID: 20260720_10_reviews
Revises: 20260720_09_transactions
Create Date: 2026-07-20 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260720_10_reviews"
down_revision: Union[str, Sequence[str], None] = "20260720_09_transactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dietitian_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dietitian_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reviews_reviewer_dietitian",
        "reviews",
        ["reviewer_id", "dietitian_id"],
        unique=True,
    )
    op.create_index(
        "ix_reviews_dietitian_id",
        "reviews",
        ["dietitian_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reviews_dietitian_id", table_name="reviews")
    op.drop_index("ix_reviews_reviewer_dietitian", table_name="reviews")
    op.drop_table("reviews")
