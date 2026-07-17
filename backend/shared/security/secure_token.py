import hashlib
import secrets


class SecureToken:
    """Shared generation logic for one-time bearer tokens (password reset,
    email verification, ...) — mint a random opaque secret, persist only its hash."""

    @staticmethod
    def generate() -> tuple[str, str]:
        raw_token = secrets.token_urlsafe(32)
        return raw_token, SecureToken.hash(raw_token)

    @staticmethod
    def hash(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
