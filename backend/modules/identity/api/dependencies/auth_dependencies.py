from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.application import LoginUserUseCase, RegisterUserUseCase
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from backend.modules.identity.infrastructure.security import BcryptPasswordHasher, JwtTokenService
from backend.shared.config import get_settings
from backend.shared.database.postgres import get_postgres_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_postgres_session() as session:
        yield session


def get_register_user_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> RegisterUserUseCase:
    repo = SqlAlchemyUserRepository(session)
    hasher = BcryptPasswordHasher()
    return RegisterUserUseCase(repo, hasher)


def get_login_user_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> LoginUserUseCase:
    settings = get_settings()
    repo = SqlAlchemyUserRepository(session)
    hasher = BcryptPasswordHasher()
    token_service = JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_ttl_minutes=settings.jwt_access_ttl_minutes,
        refresh_ttl_days=settings.jwt_refresh_ttl_days,
    )
    return LoginUserUseCase(repo, hasher, token_service)