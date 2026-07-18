from backend.modules.identity.application.ports.captcha_verifier import CaptchaVerifier
from backend.modules.identity.infrastructure.captcha.mock_captcha_verifier import MockCaptchaVerifier
from backend.modules.identity.infrastructure.captcha.turnstile_captcha_verifier import (
    TurnstileCaptchaVerifier,
)
from backend.shared.config.settings import Settings


def build_captcha_verifier(settings: Settings) -> CaptchaVerifier:
    if settings.captcha_provider == "mock":
        return MockCaptchaVerifier()

    if settings.captcha_provider == "turnstile":
        if not settings.captcha_secret_key:
            raise RuntimeError("CAPTCHA_SECRET_KEY must be set when CAPTCHA_PROVIDER=turnstile.")
        return TurnstileCaptchaVerifier(secret_key=settings.captcha_secret_key)

    raise ValueError(f"Unknown CAPTCHA_PROVIDER: {settings.captcha_provider!r} (expected mock|turnstile).")
