import os
import uuid

import pytest
from fastapi.testclient import TestClient
from redis.asyncio import Redis

from backend.shared.config import get_settings

REDIS_TEST_URL = "redis://localhost:6380/0"


@pytest.mark.asyncio
async def test_repeated_login_attempts_get_rate_limited_via_real_redis(
    redis_test_broker,
) -> None:
    """The one real-broker test for this stage: proves the fixed-window
    counter actually blocks past the configured threshold end-to-end —
    every other test in this suite runs on the default NoOpRateLimiter and
    never touches a real Redis. Flushes the shared session-scoped test
    Redis first — this container persists across every test in this file,
    so a fresh bucket can't be assumed from ordering alone."""
    flush_client = Redis.from_url(REDIS_TEST_URL)
    await flush_client.flushdb()
    await flush_client.aclose()

    os.environ["RATE_LIMIT_PROVIDER"] = "redis"
    os.environ["REDIS_URL"] = REDIS_TEST_URL
    os.environ["RATE_LIMIT_MAX_ATTEMPTS"] = "3"
    os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "60"
    get_settings.cache_clear()
    try:
        from backend.app.main import create_app

        with TestClient(create_app()) as client:
            email = f"ratelimit.{uuid.uuid4().hex[:10]}@example.com"
            payload = {"email": email, "password": "WrongPassword123"}

            statuses = [client.post("/api/v1/auth/login", json=payload).status_code for _ in range(3)]
            blocked = client.post("/api/v1/auth/login", json=payload)

            assert all(status == 401 for status in statuses)
            assert blocked.status_code == 429
            assert blocked.json()["code"] == "RATE_LIMITED"
    finally:
        os.environ.pop("RATE_LIMIT_PROVIDER", None)
        os.environ.pop("REDIS_URL", None)
        os.environ.pop("RATE_LIMIT_MAX_ATTEMPTS", None)
        os.environ.pop("RATE_LIMIT_WINDOW_SECONDS", None)
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_rate_limit_buckets_are_independent_per_action(redis_test_broker) -> None:
    """Flooding /auth/login shouldn't also block /auth/register from the
    same IP — separate counter bucket per action."""
    os.environ["RATE_LIMIT_PROVIDER"] = "redis"
    os.environ["REDIS_URL"] = REDIS_TEST_URL
    os.environ["RATE_LIMIT_MAX_ATTEMPTS"] = "3"
    os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "60"
    get_settings.cache_clear()
    try:
        from backend.app.main import create_app

        with TestClient(create_app()) as client:
            login_email = f"ratelimit.{uuid.uuid4().hex[:10]}@example.com"
            for _ in range(4):
                client.post(
                    "/api/v1/auth/login",
                    json={"email": login_email, "password": "WrongPassword123"},
                )

            register_email = f"ratelimit.{uuid.uuid4().hex[:10]}@example.com"
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": register_email,
                    "password": "StrongPass123",
                    "captcha_token": "test-captcha-token",
                },
            )

            assert response.status_code == 201
    finally:
        os.environ.pop("RATE_LIMIT_PROVIDER", None)
        os.environ.pop("REDIS_URL", None)
        os.environ.pop("RATE_LIMIT_MAX_ATTEMPTS", None)
        os.environ.pop("RATE_LIMIT_WINDOW_SECONDS", None)
        get_settings.cache_clear()
