from dataclasses import dataclass

from backend.modules.identity.domain.exceptions.identity_domain_errors import (
    InvalidDisplayNameError,
)
from backend.shared.validation import is_valid_human_name


@dataclass(frozen=True, slots=True)
class DisplayName:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not is_valid_human_name(normalized):
            raise InvalidDisplayNameError(
                "Display name must contain only letters, digits, and single spaces between them."
            )
        object.__setattr__(self, "value", normalized)
