import uuid
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from backend.modules.transactions.infrastructure.persistence.repository.sqlalchemy_transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from backend.shared.config import get_settings


@asynccontextmanager
async def test_db_session():
    """A dedicated engine, separate from the app's own (which lives on
    TestClient's portal event loop) — callers wrap this in `asyncio.run()`,
    which spins up a fresh loop per call, and asyncpg connections can't
    cross event loops."""
    engine = create_async_engine(get_settings().postgres_url, future=True)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            yield session
    finally:
        await engine.dispose()


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def register_and_login(client: TestClient, prefix: str) -> tuple[str, str]:
    email = unique_email(prefix)
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    return login.json()["access_token"], register.json()["user_id"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def promote_to_dietitian(user_id: str) -> None:
    async with test_db_session() as session:
        user_repo = SqlAlchemyUserRepository(session)
        user = await user_repo.get_by_id(UUID(user_id))
        user.change_role(Role.DIET_USER)
        await user_repo.save(user)
        await session.commit()


async def verify_email(user_id: str) -> None:
    """Phase 13 Etap 0 Stage 3's own tests need a verified buyer without
    going through the real confirm-email-verification flow (already
    covered by identity's own tests) — same direct-DB-bootstrap spirit as
    `promote_to_dietitian` above."""
    async with test_db_session() as session:
        user_repo = SqlAlchemyUserRepository(session)
        user = await user_repo.get_by_id(UUID(user_id))
        user.mark_email_verified()
        await user_repo.save(user)
        await session.commit()


async def mark_transaction_paid_directly(transaction_id: str) -> None:
    """Etap 5 Stage 1's own tests need a paid transaction without going
    through the full admin mark-paid endpoint (already covered by the
    admin module's own tests) — same direct-DB-bootstrap spirit as
    `promote_to_dietitian` above."""
    async with test_db_session() as session:
        transaction_repo = SqlAlchemyTransactionRepository(session)
        transaction = await transaction_repo.get_by_id(UUID(transaction_id))
        transaction.mark_paid()
        await transaction_repo.save(transaction)
        await session.commit()
