from dataclasses import dataclass
import re

from backend.modules.identity.domain.exceptions.identity_domain_errors import InvalidEmailError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not normalized or len(normalized) > 254 or not _EMAIL_RE.match(normalized):
            raise InvalidEmailError("Invalid email format.")
        object.__setattr__(self, "value", normalized)