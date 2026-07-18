from backend.modules.identity.application.dto.request_password_reset_dto import (
    RequestPasswordResetCommand,
)
from backend.modules.identity.application.ports.email_sender import EmailSender
from backend.modules.identity.domain import (
    Email,
    IdentityDomainError,
    PasswordResetToken,
    PasswordResetTokenRepository,
    UserRepository,
)

_RESET_TOKEN_TTL_MINUTES = 30


class RequestPasswordResetUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_reset_token_repository: PasswordResetTokenRepository,
        email_sender: EmailSender,
    ) -> None:
        self._user_repository = user_repository
        self._password_reset_token_repository = password_reset_token_repository
        self._email_sender = email_sender

    async def execute(self, command: RequestPasswordResetCommand) -> None:
        # Never reveal whether the email exists — same don't-leak-existence
        # principle used everywhere else in this module (login, refresh).
        try:
            email = Email(command.email)
        except IdentityDomainError:
            return

        user = await self._user_repository.get_by_email(email)
        if user is None:
            return

        token, raw_token = PasswordResetToken.issue(
            user_id=user.id, ttl_minutes=_RESET_TOKEN_TTL_MINUTES
        )
        await self._password_reset_token_repository.save(token)

        await self._email_sender.send(
            to=user.email.value,
            subject="Reset your Diet AI password",
            body=(
                "We received a request to reset your password.\n\n"
                f"Reset token: {raw_token}\n\n"
                f"This token expires in {_RESET_TOKEN_TTL_MINUTES} minutes. "
                "If you didn't request this, you can safely ignore this email."
            ),
            purpose="PASSWORD_RESET",
        )
