import pytest

from backend.modules.identity.api.dependencies.current_user import require_role
from backend.modules.identity.domain import Email, PasswordHash, Role, User
from backend.shared.exceptions import AppException, ErrorCode


def _build_user(role: Role) -> User:
    user = User.create(
        email=Email("role-check@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )
    user.change_role(role)
    return user


@pytest.mark.asyncio
async def test_require_role_allows_matching_role() -> None:
    user = _build_user(Role.ADMIN)

    result = await require_role(Role.ADMIN, Role.SUPER_ADMIN)(current_user=user)

    assert result is user


@pytest.mark.asyncio
async def test_require_role_allows_any_role_in_the_allowed_set() -> None:
    admin = _build_user(Role.ADMIN)
    super_admin = _build_user(Role.SUPER_ADMIN)
    dependency = require_role(Role.ADMIN, Role.SUPER_ADMIN)

    assert await dependency(current_user=admin) is admin
    assert await dependency(current_user=super_admin) is super_admin


@pytest.mark.asyncio
async def test_require_role_rejects_role_outside_allowed_set() -> None:
    user = _build_user(Role.USER)
    dependency = require_role(Role.ADMIN, Role.SUPER_ADMIN)

    with pytest.raises(AppException) as exc_info:
        await dependency(current_user=user)

    assert exc_info.value.code == ErrorCode.FORBIDDEN
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_role_rejects_diet_user_when_only_super_admin_allowed() -> None:
    user = _build_user(Role.DIET_USER)
    dependency = require_role(Role.SUPER_ADMIN)

    with pytest.raises(AppException) as exc_info:
        await dependency(current_user=user)

    assert exc_info.value.code == ErrorCode.FORBIDDEN
