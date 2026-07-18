from backend.modules.identity.application.dto.confirm_password_reset_dto import (
    ConfirmPasswordResetCommand,
)
from backend.modules.identity.application.ports.password_hasher import PasswordHasher
from backend.modules.identity.application.ports.refresh_token_repository import (
    RefreshTokenRepository,
)
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain import (
    InvalidPasswordResetTokenError,
    PasswordHash,
    PasswordPolicy,
    PasswordResetToken,
    PasswordResetTokenRepository,
    UserRepository,
)


class ConfirmPasswordResetUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_reset_token_repository: PasswordResetTokenRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repository = user_repository
        self._password_reset_token_repository = password_reset_token_repository
        self._refresh_token_repository = refresh_token_repository
        self._password_hasher = password_hasher

    async def execute(self, command: ConfirmPasswordResetCommand) -> None:
        token_hash = PasswordResetToken.hash_token(command.token)
        token = await self._password_reset_token_repository.get_by_token_hash(token_hash)
        if token is None or not token.is_valid():
            raise InvalidPasswordResetTokenError("Invalid or expired password reset token.")

        user = await self._user_repository.get_by_id(token.user_id)
        if user is None:
            raise UserNotFoundError("User not found.")

        PasswordPolicy.validate(command.new_password)
        new_hash = PasswordHash(self._password_hasher.hash(command.new_password))
        user.change_password(new_hash)
        await self._user_repository.save(user)

        token.mark_used()
        await self._password_reset_token_repository.save(token)

        # Force re-login everywhere — standard practice after a credential reset.
        await self._refresh_token_repository.revoke_all_for_user(user.id)
