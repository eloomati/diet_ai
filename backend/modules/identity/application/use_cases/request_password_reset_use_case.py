from backend.modules.identity.application.dto.request_password_reset_dto import (
    RequestPasswordResetCommand,
)
from backend.modules.identity.application.ports.captcha_verifier import CaptchaVerifier
from backend.modules.identity.application.ports.email_sender import EmailSender
from backend.modules.identity.application.use_cases.exceptions import InvalidCaptchaError
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
        captcha_verifier: CaptchaVerifier,
    ) -> None:
        self._user_repository = user_repository
        self._password_reset_token_repository = password_reset_token_repository
        self._email_sender = email_sender
        self._captcha_verifier = captcha_verifier

    async def execute(self, command: RequestPasswordResetCommand) -> None:
        # Checked before the don't-leak-existence logic below — a bad
        # captcha fails outright and reveals nothing about the email either.
        if not await self._captcha_verifier.verify(command.captcha_token):
            raise InvalidCaptchaError("CAPTCHA verification failed.")

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
            subject="Reset your Mycelo password",
            body=(
                "We received a request to reset your password.\n\n"
                f"Reset token: {raw_token}\n\n"
                f"This token expires in {_RESET_TOKEN_TTL_MINUTES} minutes. "
                "If you didn't request this, you can safely ignore this email."
            ),
            purpose="PASSWORD_RESET",
        )
