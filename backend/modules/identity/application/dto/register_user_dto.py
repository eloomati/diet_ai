from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class RegisterUserResult:
    user_id: str
    email: str