from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.nutrition.domain.entities.diet_plan import DietPlan


class DietPlanRepository(ABC):
    @abstractmethod
    async def get_by_id(self, plan_id: UUID) -> DietPlan | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user_id(self, user_id: UUID) -> list[DietPlan]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, plan: DietPlan) -> None:
        raise NotImplementedError
