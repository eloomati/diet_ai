from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.api.dependencies.auth_dependencies import get_db_session
from backend.modules.identity.domain import Role, User
from backend.modules.identity.infrastructure.persistence.repository import SqlAlchemyUserRepository
from backend.modules.identity.infrastructure.security import JwtTokenService
from backend.shared.config import get_settings
from backend.shared.exceptions import AppException, ErrorCode

bearer_scheme = HTTPBearer(auto_error=False)


def _build_token_service() -> JwtTokenService:
    settings = get_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_ttl_minutes=settings.jwt_access_ttl_minutes,
        refresh_ttl_days=settings.jwt_refresh_ttl_days,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    if not credentials:
        raise AppException(
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message="Missing bearer token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = credentials.credentials
    token_service = _build_token_service()

    try:
        payload = token_service.decode_access_token(token)
        user_id = payload["sub"]
    except Exception as exc:
        raise AppException(
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message="Invalid access token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc

    repo = SqlAlchemyUserRepository(session)
    user = await repo.get_by_id(UUID(user_id))
    if not user:
        raise AppException(
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message="User not found",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        user.assert_can_authenticate()
    except Exception as exc:
        raise AppException(
            code=ErrorCode.INACTIVE_USER,
            message="User is not active",
            status_code=status.HTTP_403_FORBIDDEN,
        ) from exc

    return user


def require_role(*roles: Role) -> Callable[[User], Awaitable[User]]:
    """Dependency factory: `Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN))`.

    Builds on `get_current_user` rather than duplicating token/session
    handling — this only adds the role check on top. Whether a given role
    transition is *itself* legal (e.g. only SUPER_ADMIN may grant ADMIN)
    is enforced by which roles a given endpoint requires, not by this
    dependency, which only ever checks "is the caller's role in the
    allowed set".
    """

    async def _require_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise AppException(
                code=ErrorCode.FORBIDDEN,
                message="You do not have permission to perform this action.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return _require_role