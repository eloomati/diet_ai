from datetime import UTC, datetime, timedelta

import jwt

from backend.modules.identity.application.ports.token_service import TokenService


class JwtTokenService(TokenService):
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_ttl_minutes: int = 15,
        refresh_ttl_days: int = 7,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_ttl_minutes = access_ttl_minutes
        self._refresh_ttl_days = refresh_ttl_days

    def create_access_token(self, user_id: str, email: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._access_ttl_minutes)).timestamp()),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=self._refresh_ttl_days)).timestamp()),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_refresh_token(self, token: str) -> dict:
        payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        if payload.get("type") != "refresh":
            raise ValueError("Token is not a refresh token")
        return payload

    def decode_access_token(self, token: str) -> dict:
        payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        if payload.get("type") != "access":
            raise ValueError("Token is not an access token")
        return payload