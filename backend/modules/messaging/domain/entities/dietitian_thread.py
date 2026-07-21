from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class DietitianThread:
    id: UUID
    user_id: UUID
    dietitian_id: UUID
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(cls, user_id: UUID, dietitian_id: UUID) -> "DietitianThread":
        return cls(id=uuid4(), user_id=user_id, dietitian_id=dietitian_id)

    def has_participant(self, user_id: UUID) -> bool:
        return user_id in (self.user_id, self.dietitian_id)

    def other_participant(self, user_id: UUID) -> UUID:
        return self.dietitian_id if user_id == self.user_id else self.user_id
