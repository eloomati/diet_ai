from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.nutrition.domain.entities.combined_diet_plan_export import (
    CombinedDietPlanExport,
)


class CombinedDietPlanExportRepository(ABC):
    @abstractmethod
    async def save(self, export: CombinedDietPlanExport) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, export_id: UUID) -> CombinedDietPlanExport | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_user_id(self, user_id: UUID) -> None:
        raise NotImplementedError
