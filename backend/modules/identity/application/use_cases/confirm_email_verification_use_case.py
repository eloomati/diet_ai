from backend.modules.identity.application.dto.confirm_email_verification_dto import (
    ConfirmEmailVerificationCommand,
)
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain import (
    EmailVerificationTokenRepository,
    InvalidEmailVerificationTokenError,
    SecureToken,
    UserRepository,
)


class ConfirmEmailVerificationUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        email_verification_token_repository: EmailVerificationTokenRepository,
    ) -> None:
        self._user_repository = user_repository
        self._email_verification_token_repository = email_verification_token_repository

    async def execute(self, command: ConfirmEmailVerificationCommand) -> None:
        token_hash = SecureToken.hash(command.token)
        token = await self._email_verification_token_repository.get_by_token_hash(token_hash)
        if token is None or not token.is_valid():
            raise InvalidEmailVerificationTokenError("Invalid or expired verification token.")

        user = await self._user_repository.get_by_id(token.user_id)
        if user is None:
            raise UserNotFoundError("User not found.")

        user.mark_email_verified()
        await self._user_repository.save(user)

        token.mark_used()
        await self._email_verification_token_repository.save(token)
