from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class CombinedDietPlanExport:
    id: UUID
    user_id: UUID
    diet_plan_ids: tuple[UUID, ...]
    filename: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls, user_id: UUID, diet_plan_ids: tuple[UUID, ...], filename: str
    ) -> "CombinedDietPlanExport":
        return cls(
            id=uuid4(),
            user_id=user_id,
            diet_plan_ids=diet_plan_ids,
            filename=filename,
            created_at=datetime.now(UTC),
        )
