from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.application import (
    LoginUserUseCase,
    RefreshAccessTokenUseCase,
    RegisterUserUseCase,
)
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from backend.modules.identity.infrastructure.security import BcryptPasswordHasher, JwtTokenService
from backend.shared.config import get_settings
from backend.shared.database.postgres import get_postgres_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_postgres_session() as session:
        yield session


def _build_token_service() -> JwtTokenService:
    settings = get_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_ttl_minutes=settings.jwt_access_ttl_minutes,
        refresh_ttl_days=settings.jwt_refresh_ttl_days,
    )


def get_register_user_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> RegisterUserUseCase:
    repo = SqlAlchemyUserRepository(session)
    hasher = BcryptPasswordHasher()
    return RegisterUserUseCase(repo, hasher)


def get_login_user_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> LoginUserUseCase:
    user_repo = SqlAlchemyUserRepository(session)
    refresh_repo = SqlAlchemyRefreshTokenRepository(session)
    hasher = BcryptPasswordHasher()
    token_service = _build_token_service()
    return LoginUserUseCase(user_repo, refresh_repo, hasher, token_service)


def get_refresh_access_token_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> RefreshAccessTokenUseCase:
    user_repo = SqlAlchemyUserRepository(session)
    refresh_repo = SqlAlchemyRefreshTokenRepository(session)
    token_service = _build_token_service()
    return RefreshAccessTokenUseCase(user_repo, refresh_repo, token_service)