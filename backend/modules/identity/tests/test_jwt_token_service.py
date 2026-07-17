import os

import jwt

from backend.modules.identity.infrastructure.security import JwtTokenService

TEST_JWT_SECRET = os.environ["JWT_SECRET_KEY"]


def test_create_access_token() -> None:
    svc = JwtTokenService(secret_key=TEST_JWT_SECRET)

    token = svc.create_access_token(user_id="u1", email="john@example.com")
    payload = jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"])

    assert payload["sub"] == "u1"
    assert payload["email"] == "john@example.com"
    assert payload["type"] == "access"


def test_create_refresh_token() -> None:
    svc = JwtTokenService(secret_key=TEST_JWT_SECRET)

    token = svc.create_refresh_token(user_id="u1")
    payload = jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"])

    assert payload["sub"] == "u1"
    assert payload["type"] == "refresh"