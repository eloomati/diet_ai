from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from backend.modules.nutrition.domain.entities.diet_plan import DietPlan


class DietPlanRepository(ABC):
    @abstractmethod
    async def get_by_id(self, plan_id: UUID) -> DietPlan | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user_id(
        self,
        user_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[DietPlan]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, plan: DietPlan) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_user_id(self, user_id: UUID) -> None:
        raise NotImplementedError
