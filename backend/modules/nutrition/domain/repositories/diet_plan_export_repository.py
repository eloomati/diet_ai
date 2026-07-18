from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.nutrition.domain.entities.diet_plan_export import DietPlanExport


class DietPlanExportRepository(ABC):
    @abstractmethod
    async def save(self, export: DietPlanExport) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, export_id: UUID) -> DietPlanExport | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_diet_plan_id(self, diet_plan_id: UUID) -> list[DietPlanExport]:
        raise NotImplementedError
