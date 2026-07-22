from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UpdateDisplayNameCommand:
    user_id: UUID
    display_name: str | None
