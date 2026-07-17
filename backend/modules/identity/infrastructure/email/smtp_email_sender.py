from email.message import EmailMessage

import aiosmtplib

from backend.modules.identity.application.ports.email_sender import EmailSender


class SmtpEmailSender(EmailSender):
    """Sends real emails over SMTP (e.g. to the dev stack's Mailhog catcher)."""

    def __init__(self, host: str, port: int, from_address: str) -> None:
        self._host = host
        self._port = port
        self._from_address = from_address

    async def send(self, to: str, subject: str, body: str, purpose: str = "") -> None:
        message = EmailMessage()
        message["From"] = self._from_address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=self._host,
            port=self._port,
            start_tls=False,
        )
