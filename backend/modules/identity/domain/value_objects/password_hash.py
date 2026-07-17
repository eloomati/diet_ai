from dataclasses import dataclass

from backend.modules.identity.domain.exceptions.identity_domain_errors import InvalidPasswordHashError


@dataclass(frozen=True, slots=True)
class PasswordHash:
    value: str

    def __post_init__(self) -> None:
        v = self.value.strip()
        if not v or (not v.startswith("$2") and not v.startswith("$argon2")):
            raise InvalidPasswordHashError("Invalid password hash format.")
        object.__setattr__(self, "value", v)