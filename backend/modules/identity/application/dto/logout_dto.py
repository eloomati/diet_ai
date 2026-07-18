from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogoutCommand:
    refresh_token: str
