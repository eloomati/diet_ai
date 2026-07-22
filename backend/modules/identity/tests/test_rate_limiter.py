import pytest

from backend.modules.identity.infrastructure.rate_limit.no_op_rate_limiter import NoOpRateLimiter
from backend.modules.identity.infrastructure.rate_limit.redis_rate_limiter import RedisRateLimiter


class FakeRedis:
    """Just enough of redis.asyncio.Redis's surface for RedisRateLimiter —
    an in-memory stand-in, no real Redis needed for this test."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}
        self.expired_keys: list[tuple[str, int]] = []

    async def incr(self, key: str) -> int:
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key]

    async def expire(self, key: str, seconds: int) -> None:
        self.expired_keys.append((key, seconds))


@pytest.mark.asyncio
async def test_no_op_rate_limiter_always_allows() -> None:
    limiter = NoOpRateLimiter()

    for _ in range(100):
        assert await limiter.hit("login:1.2.3.4", max_attempts=5, window_seconds=60) is True


@pytest.mark.asyncio
async def test_redis_rate_limiter_allows_up_to_max_attempts() -> None:
    limiter = RedisRateLimiter(FakeRedis())

    results = [
        await limiter.hit("login:1.2.3.4", max_attempts=3, window_seconds=60) for _ in range(3)
    ]

    assert results == [True, True, True]


@pytest.mark.asyncio
async def test_redis_rate_limiter_blocks_past_max_attempts() -> None:
    limiter = RedisRateLimiter(FakeRedis())

    for _ in range(3):
        await limiter.hit("login:1.2.3.4", max_attempts=3, window_seconds=60)
    blocked = await limiter.hit("login:1.2.3.4", max_attempts=3, window_seconds=60)

    assert blocked is False


@pytest.mark.asyncio
async def test_redis_rate_limiter_sets_expiry_only_on_first_hit() -> None:
    fake_redis = FakeRedis()
    limiter = RedisRateLimiter(fake_redis)

    await limiter.hit("login:1.2.3.4", max_attempts=5, window_seconds=60)
    await limiter.hit("login:1.2.3.4", max_attempts=5, window_seconds=60)

    assert fake_redis.expired_keys == [("login:1.2.3.4", 60)]


@pytest.mark.asyncio
async def test_redis_rate_limiter_keeps_separate_counters_per_key() -> None:
    limiter = RedisRateLimiter(FakeRedis())

    for _ in range(3):
        await limiter.hit("login:1.2.3.4", max_attempts=3, window_seconds=60)
    still_allowed = await limiter.hit("register:1.2.3.4", max_attempts=3, window_seconds=60)

    assert still_allowed is True
