import uuid
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread
from backend.modules.messaging.infrastructure.persistence.repository.sqlalchemy_dietitian_thread_repository import (
    SqlAlchemyDietitianThreadRepository,
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


async def create_thread_directly(user_id: str, dietitian_id: str) -> str:
    """Notifications' own tests need an existing thread to send a real
    message through (which is what actually creates a NEW_MESSAGE
    notification) — same direct-DB-bootstrap spirit as
    `messaging.tests.db_helpers.create_thread_directly`."""
    async with test_db_session() as session:
        thread_repo = SqlAlchemyDietitianThreadRepository(session)
        thread = DietitianThread.create(user_id=UUID(user_id), dietitian_id=UUID(dietitian_id))
        await thread_repo.save(thread)
        await session.commit()
        return str(thread.id)
