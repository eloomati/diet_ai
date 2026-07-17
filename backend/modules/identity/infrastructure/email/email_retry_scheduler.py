import asyncio
import logging

from backend.modules.identity.application.use_cases.email_retry_strategies import (
    EmailVerificationRetryStrategy,
    PasswordResetRetryStrategy,
)
from backend.modules.identity.application.use_cases.retry_failed_emails_use_case import (
    RetryFailedEmailsUseCase,
)
from backend.modules.identity.infrastructure.email.email_sender_factory import build_email_sender
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_email_log_repository import (
    SqlAlchemyEmailLogRepository,
)
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_email_verification_token_repository import (
    SqlAlchemyEmailVerificationTokenRepository,
)
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_password_reset_token_repository import (
    SqlAlchemyPasswordResetTokenRepository,
)
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from backend.shared.config.settings import Settings
from backend.shared.database.postgres import get_postgres_session

logger = logging.getLogger(__name__)


async def _run_one_retry_pass(settings: Settings) -> int:
    async with get_postgres_session() as session:
        email_log_repository = SqlAlchemyEmailLogRepository(session)
        user_repository = SqlAlchemyUserRepository(session)
        base_sender = build_email_sender(settings)
        use_case = RetryFailedEmailsUseCase(
            email_log_repository=email_log_repository,
            user_repository=user_repository,
            email_sender=base_sender,
            strategies={
                "PASSWORD_RESET": PasswordResetRetryStrategy(
                    SqlAlchemyPasswordResetTokenRepository(session)
                ),
                "EMAIL_VERIFICATION": EmailVerificationRetryStrategy(
                    SqlAlchemyEmailVerificationTokenRepository(session)
                ),
            },
            max_attempts=settings.email_retry_max_attempts,
            retry_interval_seconds=settings.email_retry_interval_seconds,
            batch_limit=settings.email_retry_batch_limit,
        )
        retried = await use_case.execute()
        await session.commit()
        return retried


async def run_email_retry_loop(settings: Settings) -> None:
    """Background timer: every `email_retry_interval_seconds`, retries FAILED
    email_logs rows that are due. Runs as an asyncio task for the app's lifetime —
    no broker/queue exists in this stack, and a single periodic job doesn't justify
    adding one."""
    while True:
        try:
            retried = await _run_one_retry_pass(settings)
            if retried:
                logger.info("Email retry pass: attempted %d failed email(s).", retried)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Email retry loop iteration failed.")
        await asyncio.sleep(settings.email_retry_interval_seconds)
