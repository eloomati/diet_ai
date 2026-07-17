from datetime import UTC, datetime, timedelta

from backend.modules.identity.application.dto.login_user_dto import (
    LoginUserCommand,
    LoginUserResult,
)
from backend.modules.identity.application.ports.password_hasher import PasswordHasher
from backend.modules.identity.application.ports.refresh_token_repository import RefreshTokenRepository
from backend.modules.identity.application.ports.token_service import TokenService
from backend.modules.identity.application.use_cases.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
)
from backend.modules.identity.domain import Email, RefreshToken, UserRepository


class LoginUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        refresh_ttl_days: int = 7,
    ) -> None:
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._refresh_ttl_days = refresh_ttl_days

    async def execute(self, command: LoginUserCommand) -> LoginUserResult:
        email = Email(command.email)
        user = await self._user_repository.get_by_email(email)

        if not user:
            raise UserNotFoundError("User not found.")

        user.assert_can_authenticate()

        is_valid = self._password_hasher.verify(command.password, user.password_hash.value)
        if not is_valid:
            raise InvalidCredentialsError("Invalid credentials.")

        user.mark_logged_in()
        await self._user_repository.save(user)

        access_token = self._token_service.create_access_token(
            user_id=str(user.id),
            email=user.email.value,
        )
        refresh_token = self._token_service.create_refresh_token(str(user.id))

        refresh_entity = RefreshToken.issue(
            user_id=user.id,
            token_hash=refresh_token,
            expires_at=datetime.now(UTC) + timedelta(days=self._refresh_ttl_days),
        )
        await self._refresh_token_repository.save(refresh_entity)

        return LoginUserResult(
            access_token=access_token,
            refresh_token=refresh_token,
        )