from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfirmPasswordResetCommand:
    token: str
    new_password: str
