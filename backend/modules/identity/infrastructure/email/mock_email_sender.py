from dataclasses import dataclass

from backend.modules.identity.application.ports.email_sender import EmailSender


@dataclass(frozen=True, slots=True)
class SentEmail:
    to: str
    subject: str
    body: str
    purpose: str = ""


class MockEmailSender(EmailSender):
    """Deterministic dev/test provider — no network calls, no real SMTP server needed."""

    def __init__(self) -> None:
        self.sent: list[SentEmail] = []

    async def send(self, to: str, subject: str, body: str, purpose: str = "") -> None:
        self.sent.append(SentEmail(to=to, subject=subject, body=body, purpose=purpose))
