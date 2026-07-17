from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfirmEmailVerificationCommand:
    token: str
