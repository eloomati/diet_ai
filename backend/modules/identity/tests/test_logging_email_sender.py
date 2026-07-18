import pytest

from backend.modules.identity.domain.entities.email_log import EmailDeliveryStatus
from backend.modules.identity.infrastructure.email.logging_email_sender import LoggingEmailSender
from backend.modules.identity.tests.fakes import FakeEmailSender, InMemoryEmailLogRepository


@pytest.mark.asyncio
async def test_successful_send_is_logged_as_sent_and_delegates_to_inner() -> None:
    inner = FakeEmailSender()
    log_repo = InMemoryEmailLogRepository()
    sender = LoggingEmailSender(inner, log_repo)

    await sender.send("user@example.com", "Subject", "Body", purpose="EMAIL_VERIFICATION")

    assert len(inner.sent) == 1
    assert inner.sent[0].body == "Body"
    assert len(log_repo.saved) == 1
    log = log_repo.saved[0]
    assert log.to == "user@example.com"
    assert log.subject == "Subject"
    assert log.purpose == "EMAIL_VERIFICATION"
    assert log.status == EmailDeliveryStatus.SENT
    assert log.error_message is None


@pytest.mark.asyncio
async def test_failed_send_is_logged_as_failed_and_reraises() -> None:
    class BrokenEmailSender:
        async def send(self, to: str, subject: str, body: str, purpose: str) -> None:
            raise RuntimeError("SMTP connection refused")

    log_repo = InMemoryEmailLogRepository()
    sender = LoggingEmailSender(BrokenEmailSender(), log_repo)

    with pytest.raises(RuntimeError, match="SMTP connection refused"):
        await sender.send("user@example.com", "Subject", "Body", purpose="PASSWORD_RESET")

    assert len(log_repo.saved) == 1
    log = log_repo.saved[0]
    assert log.status == EmailDeliveryStatus.FAILED
    assert log.error_message == "SMTP connection refused"


@pytest.mark.asyncio
async def test_log_never_records_the_email_body() -> None:
    inner = FakeEmailSender()
    log_repo = InMemoryEmailLogRepository()
    sender = LoggingEmailSender(inner, log_repo)

    await sender.send("user@example.com", "Subject", "super-secret-token-in-body", purpose="X")

    log = log_repo.saved[0]
    assert not hasattr(log, "body")
