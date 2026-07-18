import pytest

from backend.modules.identity.application import (
    InvalidCredentialsError,
    LoginUserCommand,
    LoginUserUseCase,
    RegisterUserCommand,
    RegisterUserUseCase,
    UserNotFoundError,
)
from backend.modules.identity.tests.fakes import (
    FakeEmailSender,
    FakePasswordHasher,
    FakeTokenService,
    InMemoryEmailVerificationTokenRepository,
    InMemoryRefreshTokenRepository,
    InMemoryUserRepository,
)


@pytest.mark.asyncio
async def test_login_success() -> None:
    repo = InMemoryUserRepository()
    refresh_repo = InMemoryRefreshTokenRepository()
    hasher = FakePasswordHasher()
    tokens = FakeTokenService()

    register_uc = RegisterUserUseCase(
        repo, hasher, InMemoryEmailVerificationTokenRepository(), FakeEmailSender()
    )
    login_uc = LoginUserUseCase(repo, refresh_repo, hasher, tokens)

    await register_uc.execute(
        RegisterUserCommand(
            email="john@example.com",
            password="StrongPass123",
        )
    )

    result = await login_uc.execute(
        LoginUserCommand(
            email="john@example.com",
            password="StrongPass123",
        )
    )

    assert result.access_token.startswith("access::")
    assert result.refresh_token.startswith("refresh::")
    assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_login_user_not_found() -> None:
    repo = InMemoryUserRepository()
    refresh_repo = InMemoryRefreshTokenRepository()
    hasher = FakePasswordHasher()
    tokens = FakeTokenService()
    login_uc = LoginUserUseCase(repo, refresh_repo, hasher, tokens)

    with pytest.raises(UserNotFoundError):
        await login_uc.execute(
            LoginUserCommand(
                email="missing@example.com",
                password="StrongPass123",
            )
        )


@pytest.mark.asyncio
async def test_login_invalid_credentials() -> None:
    repo = InMemoryUserRepository()
    refresh_repo = InMemoryRefreshTokenRepository()
    hasher = FakePasswordHasher()
    tokens = FakeTokenService()

    register_uc = RegisterUserUseCase(
        repo, hasher, InMemoryEmailVerificationTokenRepository(), FakeEmailSender()
    )
    login_uc = LoginUserUseCase(repo, refresh_repo, hasher, tokens)

    await register_uc.execute(
        RegisterUserCommand(
            email="john@example.com",
            password="StrongPass123",
        )
    )

    with pytest.raises(InvalidCredentialsError):
        await login_uc.execute(
            LoginUserCommand(
                email="john@example.com",
                password="WrongPass123",
            )
        )