from redis.asyncio import Redis

# Module-level singleton, same shape as backend/shared/messaging/kafka.py's
# producer — initialized in the app's lifespan, not per-request.
_client: Redis | None = None


async def init_redis_client(url: str) -> None:
    global _client

    _client = Redis.from_url(url)
    await _client.ping()


async def close_redis_client() -> None:
    global _client

    if _client is not None:
        await _client.aclose()
        _client = None


def get_redis_client() -> Redis:
    if _client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis_client() in lifespan.")
    return _client
