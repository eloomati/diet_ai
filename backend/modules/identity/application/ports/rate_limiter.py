from abc import ABC, abstractmethod


class RateLimiter(ABC):
    @abstractmethod
    async def hit(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        """Records one attempt under `key` and returns whether it's still
        within the allowed rate — `True` if allowed, `False` if the caller
        should be blocked."""
        raise NotImplementedError
