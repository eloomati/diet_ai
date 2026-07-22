from backend.modules.identity.application.ports.rate_limiter import RateLimiter
from backend.modules.identity.infrastructure.rate_limit.no_op_rate_limiter import NoOpRateLimiter
from backend.modules.identity.infrastructure.rate_limit.redis_rate_limiter import RedisRateLimiter
from backend.shared.config.settings import Settings
from backend.shared.redis import get_redis_client


def build_rate_limiter(settings: Settings) -> RateLimiter:
    if settings.rate_limit_provider == "mock":
        return NoOpRateLimiter()

    if settings.rate_limit_provider == "redis":
        return RedisRateLimiter(get_redis_client())

    raise ValueError(
        f"Unknown RATE_LIMIT_PROVIDER: {settings.rate_limit_provider!r} (expected mock|redis)."
    )
