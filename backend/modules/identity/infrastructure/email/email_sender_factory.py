from backend.modules.identity.application.ports.email_sender import EmailSender
from backend.modules.identity.infrastructure.email.mock_email_sender import MockEmailSender
from backend.modules.identity.infrastructure.email.smtp_email_sender import SmtpEmailSender
from backend.shared.config.settings import Settings


def build_email_sender(settings: Settings) -> EmailSender:
    if settings.email_provider == "mock":
        return MockEmailSender()

    if settings.email_provider == "smtp":
        return SmtpEmailSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            from_address=settings.smtp_from_address,
        )

    raise ValueError(f"Unknown EMAIL_PROVIDER: {settings.email_provider!r} (expected mock|smtp).")


# Same singleton-lifecycle shape as ai/infrastructure/provider_factory.py — built once
# at app startup and reused across requests.
_email_sender: EmailSender | None = None


async def init_email_sender(settings: Settings) -> None:
    global _email_sender
    _email_sender = build_email_sender(settings)


async def close_email_sender() -> None:
    global _email_sender
    _email_sender = None


def get_email_sender() -> EmailSender:
    if _email_sender is None:
        raise RuntimeError("Email sender not initialized — call init_email_sender() during app startup.")
    return _email_sender
