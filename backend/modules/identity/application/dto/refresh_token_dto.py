from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RefreshTokenCommand:
    refresh_token: str


@dataclass(frozen=True, slots=True)
class RefreshTokenResult:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"