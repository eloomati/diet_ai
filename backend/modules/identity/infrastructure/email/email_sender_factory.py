from backend.modules.identity.application.ports.email_sender import EmailSender
from backend.modules.identity.infrastructure.email.mock_email_sender import MockEmailSender
from backend.modules.identity.infrastructure.email.smtp_email_sender import SmtpEmailSender
from backend.shared.config.settings import Settings


def build_email_sender(settings: Settings) -> EmailSender:
    """Builds the "base" sender (no logging). Constructed per-request, not a
    singleton — see LoggingEmailSender, which wraps this with a per-request
    Postgres session to write EmailLog rows. Unlike the Mongo client or the
    LLM provider's HTTP client, there is no persistent connection here worth
    reusing across requests: aiosmtplib opens/closes a connection per send."""
    if settings.email_provider == "mock":
        return MockEmailSender()

    if settings.email_provider == "smtp":
        return SmtpEmailSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            from_address=settings.smtp_from_address,
        )

    raise ValueError(f"Unknown EMAIL_PROVIDER: {settings.email_provider!r} (expected mock|smtp).")
