from datetime import UTC, datetime, timedelta

import jwt

from backend.modules.identity.application.ports.token_service import TokenService


class JwtTokenService(TokenService):
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_minutes: int = 15,
        refresh_token_days: int = 7,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_minutes = access_token_minutes
        self._refresh_token_days = refresh_token_days

    def create_access_token(self, user_id: str, email: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._access_token_minutes)).timestamp()),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=self._refresh_token_days)).timestamp()),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)