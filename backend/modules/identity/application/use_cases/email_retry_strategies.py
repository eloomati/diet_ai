from abc import ABC, abstractmethod

from backend.modules.identity.domain.entities.email_verification_token import (
    EmailVerificationToken,
)
from backend.modules.identity.domain.entities.password_reset_token import PasswordResetToken
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.repositories.email_verification_token_repository import (
    EmailVerificationTokenRepository,
)
from backend.modules.identity.domain.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)

_PASSWORD_RESET_TTL_MINUTES = 30
_EMAIL_VERIFICATION_TTL_MINUTES = 60 * 24


class EmailRetryStrategy(ABC):
    """Regenerates the notification for a retry attempt. Never resends the original
    body — the raw secret it once carried was never persisted (see EmailLog), so a
    retry mints a brand-new token for the same purpose instead."""

    @abstractmethod
    async def resend(self, user: User) -> tuple[str, str]:
        """Returns (subject, body) for the freshly issued notification."""
        raise NotImplementedError


class PasswordResetRetryStrategy(EmailRetryStrategy):
    def __init__(self, password_reset_token_repository: PasswordResetTokenRepository) -> None:
        self._password_reset_token_repository = password_reset_token_repository

    async def resend(self, user: User) -> tuple[str, str]:
        token, raw_token = PasswordResetToken.issue(
            user_id=user.id, ttl_minutes=_PASSWORD_RESET_TTL_MINUTES
        )
        await self._password_reset_token_repository.save(token)
        subject = "Reset your Mycelo password"
        body = (
            "We received a request to reset your password.\n\n"
            f"Reset token: {raw_token}\n\n"
            f"This token expires in {_PASSWORD_RESET_TTL_MINUTES} minutes. "
            "If you didn't request this, you can safely ignore this email."
        )
        return subject, body


class EmailVerificationRetryStrategy(EmailRetryStrategy):
    def __init__(
        self, email_verification_token_repository: EmailVerificationTokenRepository
    ) -> None:
        self._email_verification_token_repository = email_verification_token_repository

    async def resend(self, user: User) -> tuple[str, str]:
        token, raw_token = EmailVerificationToken.issue(
            user_id=user.id, ttl_minutes=_EMAIL_VERIFICATION_TTL_MINUTES
        )
        await self._email_verification_token_repository.save(token)
        subject = "Verify your Mycelo email address"
        body = (
            "Welcome to Mycelo! Please verify your email address.\n\n"
            f"Verification code: {raw_token}\n\n"
            f"This code expires in {_EMAIL_VERIFICATION_TTL_MINUTES // 60} hours."
        )
        return subject, body
