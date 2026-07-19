import httpx

from backend.modules.identity.application.ports.captcha_verifier import CaptchaVerifier

_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class TurnstileCaptchaVerifier(CaptchaVerifier):
    """Cloudflare Turnstile — chosen over reCAPTCHA for the simpler API and
    no Google account requirement. Accepts an injectable client so tests
    never make a real network call, same pattern as ClaudeProvider/OllamaProvider."""

    def __init__(self, secret_key: str, client: httpx.AsyncClient | None = None) -> None:
        self._secret_key = secret_key
        self._client = client or httpx.AsyncClient()

    async def verify(self, token: str) -> bool:
        if not token:
            return False

        response = await self._client.post(
            _SITEVERIFY_URL,
            data={"secret": self._secret_key, "response": token},
        )
        response.raise_for_status()
        body = response.json()
        return bool(body.get("success"))
