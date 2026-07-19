import asyncio
import uuid
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.infrastructure.persistence.repository.sqlalchemy_dietitian_profile_repository import (
    SqlAlchemyDietitianProfileRepository,
)
from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from backend.shared.config import get_settings


@asynccontextmanager
async def _test_db_session():
    """A dedicated engine, separate from the app's own (which lives on
    TestClient's portal event loop) — `asyncio.run()` below spins up a fresh
    loop per call, and asyncpg connections can't cross event loops."""
    engine = create_async_engine(get_settings().postgres_url, future=True)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            yield session
    finally:
        await engine.dispose()


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def _register_and_login(client: TestClient, prefix: str) -> tuple[str, str]:
    email = unique_email(prefix)
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    return login.json()["access_token"], register.json()["user_id"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _promote_to_dietitian_with_profile(user_id: str) -> None:
    """Etap 2 (admin approval) is what will normally create the
    `DietitianProfile` row and grant `DIET_USER` — it doesn't exist yet, so
    tests for this stage seed both directly against Postgres instead."""
    async with _test_db_session() as session:
        user_repo = SqlAlchemyUserRepository(session)
        user = await user_repo.get_by_id(UUID(user_id))
        user.change_role(Role.DIET_USER)
        await user_repo.save(user)

        profile_repo = SqlAlchemyDietitianProfileRepository(session)
        profile = DietitianProfile.create(
            user_id=UUID(user_id),
            experience="5 years experience",
            diplomas=("MSc Dietetics",),
            description="Weight management specialist.",
        )
        await profile_repo.save(profile)

        await session.commit()


def _upload(client: TestClient, token: str, filename: str = "photo.jpg", content_type: str = "image/jpeg"):
    return client.post(
        "/api/v1/dietitian/profile/photos",
        headers=_auth_headers(token),
        files={"file": (filename, b"fake-bytes", content_type)},
    )


def test_upload_photo_returns_201_and_updates_profile(client: TestClient) -> None:
    token, user_id = _register_and_login(client, "dietitian.photo")
    asyncio.run(_promote_to_dietitian_with_profile(user_id))

    response = _upload(client, token)

    assert response.status_code == 201
    body = response.json()
    assert len(body["photos"]) == 1
    assert body["photos"][0].startswith("/static/dietitian-photos/")


def test_upload_photo_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/dietitian/profile/photos",
        files={"file": ("photo.jpg", b"fake-bytes", "image/jpeg")},
    )

    assert response.status_code == 401


def test_upload_photo_requires_diet_user_role(client: TestClient) -> None:
    token, _ = _register_and_login(client, "dietitian.norole")

    response = _upload(client, token)

    assert response.status_code == 403


def test_upload_photo_returns_404_without_a_profile(client: TestClient) -> None:
    token, user_id = _register_and_login(client, "dietitian.noprofile")

    async def _promote_only() -> None:
        async with _test_db_session() as session:
            user_repo = SqlAlchemyUserRepository(session)
            user = await user_repo.get_by_id(UUID(user_id))
            user.change_role(Role.DIET_USER)
            await user_repo.save(user)
            await session.commit()

    asyncio.run(_promote_only())

    response = _upload(client, token)

    assert response.status_code == 404


def test_upload_photo_rejects_unsupported_content_type(client: TestClient) -> None:
    token, user_id = _register_and_login(client, "dietitian.badtype")
    asyncio.run(_promote_to_dietitian_with_profile(user_id))

    response = _upload(client, token, filename="doc.pdf", content_type="application/pdf")

    assert response.status_code == 400


def test_upload_photo_rejects_a_fourth_photo(client: TestClient) -> None:
    token, user_id = _register_and_login(client, "dietitian.fourth")
    asyncio.run(_promote_to_dietitian_with_profile(user_id))

    _upload(client, token)
    _upload(client, token)
    _upload(client, token)
    response = _upload(client, token)

    assert response.status_code == 400
