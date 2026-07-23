from backend.modules.identity.application.ports.rate_limiter import RateLimiter


class NoOpRateLimiter(RateLimiter):
    """Default (dev/test) provider — never blocks, no Redis needed. Same
    mock/real split as ai_provider/email_provider/sftp_provider/kafka_provider."""

    async def hit(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        return True
