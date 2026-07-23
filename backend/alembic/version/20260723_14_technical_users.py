"""seed technical/demo users for every role (USER, DIET_USER, ADMIN, SUPER_ADMIN)

Revision ID: 20260723_14_technical_users
Revises: 20260722_13_display_names
Create Date: 2026-07-23 10:00:00
"""

from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260723_14_technical_users"
down_revision: Union[str, Sequence[str], None] = "20260722_13_display_names"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed ids so upgrade/downgrade are deterministic and idempotent-by-intent.
USER_ID = "00000000-0000-0000-0000-000000000001"
DIETITIAN_ID = "00000000-0000-0000-0000-000000000002"
ADMIN_ID = "00000000-0000-0000-0000-000000000003"
SUPERADMIN_ID = "00000000-0000-0000-0000-000000000004"
DIETITIAN_PROFILE_ID = "00000000-0000-0000-0000-000000000005"

# bcrypt hash of "DemoPass123!" — same password for all four, documented in
# README.md alongside these accounts.
PASSWORD_HASH = "$2b$12$lYaf5Efmdx5G5JCOEqmRC.WYWmgaf.IfwNCySYS5MOLJDCw2JDPsq"

users_table = sa.table(
    "users",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("email", sa.String),
    sa.column("password_hash", sa.String),
    sa.column("status", sa.String),
    sa.column("role", sa.String),
    sa.column("email_verified", sa.Boolean),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

dietitian_profiles_table = sa.table(
    "dietitian_profiles",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("user_id", postgresql.UUID(as_uuid=True)),
    sa.column("experience", sa.Text),
    sa.column("diplomas", postgresql.ARRAY(sa.String())),
    sa.column("description", sa.Text),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    now = datetime.now(UTC)
    op.bulk_insert(
        users_table,
        [
            {
                "id": USER_ID,
                "email": "demo.user@example.com",
                "password_hash": PASSWORD_HASH,
                "status": "ACTIVE",
                "role": "USER",
                "email_verified": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": DIETITIAN_ID,
                "email": "demo.dietitian@example.com",
                "password_hash": PASSWORD_HASH,
                "status": "ACTIVE",
                "role": "DIET_USER",
                "email_verified": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": ADMIN_ID,
                "email": "demo.admin@example.com",
                "password_hash": PASSWORD_HASH,
                "status": "ACTIVE",
                "role": "ADMIN",
                "email_verified": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": SUPERADMIN_ID,
                "email": "demo.superadmin@example.com",
                "password_hash": PASSWORD_HASH,
                "status": "ACTIVE",
                "role": "SUPER_ADMIN",
                "email_verified": True,
                "created_at": now,
                "updated_at": now,
            },
        ],
    )

    # The DIET_USER demo account needs a DietitianProfile too, or
    # GET /dietitian/profile/me 404s and it won't appear in the marketplace.
    op.bulk_insert(
        dietitian_profiles_table,
        [
            {
                "id": DIETITIAN_PROFILE_ID,
                "user_id": DIETITIAN_ID,
                "experience": "5 lat doświadczenia klinicznego",
                "diplomas": ["MSc Dietetyki"],
                "description": "Konto techniczne dietetyka do celów demonstracyjnych/testowych.",
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM dietitian_profiles WHERE id = '{DIETITIAN_PROFILE_ID}'")
    op.execute(
        f"DELETE FROM users WHERE id IN "
        f"('{USER_ID}', '{DIETITIAN_ID}', '{ADMIN_ID}', '{SUPERADMIN_ID}')"
    )
