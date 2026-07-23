from dataclasses import dataclass
from uuid import UUID

from backend.modules.identity.domain.value_objects.role import Role


@dataclass(frozen=True, slots=True)
class ChangeUserRoleCommand:
    user_id: UUID
    new_role: Role
