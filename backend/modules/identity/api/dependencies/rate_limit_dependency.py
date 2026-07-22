from collections.abc import Awaitable, Callable

from fastapi import Depends, Request, status

from backend.modules.identity.application.ports.rate_limiter import RateLimiter
from backend.modules.identity.infrastructure.rate_limit.rate_limiter_factory import (
    build_rate_limiter,
)
from backend.shared.config import get_settings
from backend.shared.exceptions import AppException, ErrorCode


def get_rate_limiter() -> RateLimiter:
    return build_rate_limiter(get_settings())


def rate_limited(action: str) -> Callable[..., Awaitable[None]]:
    """Dependency factory: `Depends(rate_limited("login"))`.

    One counter bucket per action per client IP — a login flood doesn't
    also throttle registration from the same IP, and vice versa. The
    default `NoOpRateLimiter` never blocks, so tests never need a real
    Redis (same convention as `require_role` building on `get_current_user`
    rather than duplicating auth handling).
    """

    async def _rate_limited(
        request: Request,
        rate_limiter: RateLimiter = Depends(get_rate_limiter),
    ) -> None:
        settings = get_settings()
        client_ip = request.client.host if request.client else "unknown"
        allowed = await rate_limiter.hit(
            key=f"{action}:{client_ip}",
            max_attempts=settings.rate_limit_max_attempts,
            window_seconds=settings.rate_limit_window_seconds,
        )
        if not allowed:
            raise AppException(
                code=ErrorCode.RATE_LIMITED,
                message="Too many attempts. Please try again later.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    return _rate_limited
