import uuid
from datetime import UTC, datetime, timedelta

import pytest

from backend.modules.identity.application.dto.logout_dto import LogoutCommand
from backend.modules.identity.application.use_cases.logout_use_case import LogoutUseCase
from backend.modules.identity.domain.entities.refresh_token import RefreshToken
from backend.modules.identity.tests.fakes import InMemoryRefreshTokenRepository


@pytest.mark.asyncio
async def test_logout_revokes_active_refresh_token() -> None:
    repo = InMemoryRefreshTokenRepository()
    token = RefreshToken.issue(
        user_id=uuid.uuid4(),
        token_hash="raw-refresh-token",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    await repo.save(token)
    use_case = LogoutUseCase(repo)

    await use_case.execute(LogoutCommand(refresh_token="raw-refresh-token"))

    assert await repo.get_active_by_token_hash("raw-refresh-token") is None


@pytest.mark.asyncio
async def test_logout_with_unknown_token_is_a_silent_no_op() -> None:
    repo = InMemoryRefreshTokenRepository()
    use_case = LogoutUseCase(repo)

    await use_case.execute(LogoutCommand(refresh_token="never-issued"))


@pytest.mark.asyncio
async def test_logout_twice_with_same_token_is_idempotent() -> None:
    repo = InMemoryRefreshTokenRepository()
    token = RefreshToken.issue(
        user_id=uuid.uuid4(),
        token_hash="raw-refresh-token",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    await repo.save(token)
    use_case = LogoutUseCase(repo)

    await use_case.execute(LogoutCommand(refresh_token="raw-refresh-token"))
    await use_case.execute(LogoutCommand(refresh_token="raw-refresh-token"))

    assert await repo.get_active_by_token_hash("raw-refresh-token") is None
