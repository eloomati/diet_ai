from typing import Protocol

from backend.modules.identity.application.ports.rate_limiter import RateLimiter


class _RedisLike(Protocol):
    """Just the two methods this class actually calls — lets tests pass a
    fake without needing a real redis.asyncio.Redis instance."""

    async def incr(self, key: str) -> int: ...
    async def expire(self, key: str, seconds: int) -> object: ...


class RedisRateLimiter(RateLimiter):
    """Fixed-window counter: INCR the key, and if this was the first hit in
    the window, set its expiry — not a sliding-window/token-bucket
    algorithm. A small window-boundary imprecision is an acceptable
    tradeoff for a demo-scoped anti-brute-force guard. Takes the client as
    a constructor dependency (same convention as
    KafkaTransactionEventPublisher taking its producer) rather than
    reaching into the shared singleton itself."""

    def __init__(self, client: _RedisLike) -> None:
        self._client = client

    async def hit(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        count = await self._client.incr(key)
        if count == 1:
            await self._client.expire(key, window_seconds)
        return count <= max_attempts
