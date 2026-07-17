from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoginUserCommand:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class LoginUserResult:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"