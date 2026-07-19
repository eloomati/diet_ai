from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.application import (
    ChangeUserRoleUseCase,
    ConfirmEmailVerificationUseCase,
    ConfirmPasswordResetUseCase,
    LoginUserUseCase,
    LogoutUseCase,
    RefreshAccessTokenUseCase,
    RegisterUserUseCase,
    RequestPasswordResetUseCase,
)
from backend.modules.identity.application.ports.captcha_verifier import CaptchaVerifier
from backend.modules.identity.application.ports.email_sender import EmailSender
from backend.modules.identity.infrastructure.captcha.captcha_verifier_factory import (
    build_captcha_verifier,
)
from backend.modules.identity.infrastructure.email.email_sender_factory import build_email_sender
from backend.modules.identity.infrastructure.email.logging_email_sender import LoggingEmailSender
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_email_log_repository import (
    SqlAlchemyEmailLogRepository,
)
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_email_verification_token_repository import (
    SqlAlchemyEmailVerificationTokenRepository,
)
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_password_reset_token_repository import (
    SqlAlchemyPasswordResetTokenRepository,
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
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _build_token_service() -> JwtTokenService:
    settings = get_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_ttl_minutes=settings.jwt_access_ttl_minutes,
        refresh_ttl_days=settings.jwt_refresh_ttl_days,
    )


def get_email_sender(session: AsyncSession = Depends(get_db_session)) -> EmailSender:
    # Per-request, not a singleton — LoggingEmailSender needs this request's own
    # Postgres session to write an EmailLog row (see email_sender_factory.py).
    settings = get_settings()
    base_sender = build_email_sender(settings)
    email_log_repo = SqlAlchemyEmailLogRepository(session)
    return LoggingEmailSender(
        base_sender,
        email_log_repo,
        max_attempts=settings.email_retry_max_attempts,
        retry_interval_seconds=settings.email_retry_interval_seconds,
    )


def get_captcha_verifier() -> CaptchaVerifier:
    # No per-request state needed (no DB session, no request-scoped resource)
    # unlike get_email_sender — safe to build fresh per request regardless.
    return build_captcha_verifier(get_settings())


def get_register_user_use_case(
    session: AsyncSession = Depends(get_db_session),
    email_sender: EmailSender = Depends(get_email_sender),
    captcha_verifier: CaptchaVerifier = Depends(get_captcha_verifier),
) -> RegisterUserUseCase:
    repo = SqlAlchemyUserRepository(session)
    hasher = BcryptPasswordHasher()
    email_verification_repo = SqlAlchemyEmailVerificationTokenRepository(session)
    return RegisterUserUseCase(repo, hasher, email_verification_repo, email_sender, captcha_verifier)


def get_login_user_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> LoginUserUseCase:
    settings = get_settings()
    user_repo = SqlAlchemyUserRepository(session)
    refresh_repo = SqlAlchemyRefreshTokenRepository(session)
    hasher = BcryptPasswordHasher()
    token_service = _build_token_service()
    return LoginUserUseCase(
        user_repo,
        refresh_repo,
        hasher,
        token_service,
        refresh_ttl_days=settings.jwt_refresh_ttl_days,
    )


def get_refresh_access_token_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> RefreshAccessTokenUseCase:
    settings = get_settings()
    user_repo = SqlAlchemyUserRepository(session)
    refresh_repo = SqlAlchemyRefreshTokenRepository(session)
    token_service = _build_token_service()
    return RefreshAccessTokenUseCase(
        user_repo,
        refresh_repo,
        token_service,
        refresh_ttl_days=settings.jwt_refresh_ttl_days,
    )


def get_request_password_reset_use_case(
    session: AsyncSession = Depends(get_db_session),
    email_sender: EmailSender = Depends(get_email_sender),
    captcha_verifier: CaptchaVerifier = Depends(get_captcha_verifier),
) -> RequestPasswordResetUseCase:
    user_repo = SqlAlchemyUserRepository(session)
    reset_token_repo = SqlAlchemyPasswordResetTokenRepository(session)
    return RequestPasswordResetUseCase(user_repo, reset_token_repo, email_sender, captcha_verifier)


def get_confirm_password_reset_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> ConfirmPasswordResetUseCase:
    user_repo = SqlAlchemyUserRepository(session)
    reset_token_repo = SqlAlchemyPasswordResetTokenRepository(session)
    refresh_repo = SqlAlchemyRefreshTokenRepository(session)
    hasher = BcryptPasswordHasher()
    return ConfirmPasswordResetUseCase(user_repo, reset_token_repo, refresh_repo, hasher)


def get_confirm_email_verification_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> ConfirmEmailVerificationUseCase:
    user_repo = SqlAlchemyUserRepository(session)
    verification_repo = SqlAlchemyEmailVerificationTokenRepository(session)
    return ConfirmEmailVerificationUseCase(user_repo, verification_repo)


def get_logout_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> LogoutUseCase:
    refresh_repo = SqlAlchemyRefreshTokenRepository(session)
    return LogoutUseCase(refresh_repo)


def get_change_user_role_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> ChangeUserRoleUseCase:
    user_repo = SqlAlchemyUserRepository(session)
    return ChangeUserRoleUseCase(user_repo)