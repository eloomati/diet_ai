from backend.modules.identity.application.ports.captcha_verifier import CaptchaVerifier


class MockCaptchaVerifier(CaptchaVerifier):
    """Always passes — no external dependency. Default in dev/tests, same
    reasoning as MockEmailSender/MockSftpClient."""

    async def verify(self, token: str) -> bool:
        return True
