from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RequestPasswordResetCommand:
    email: str
    captcha_token: str
