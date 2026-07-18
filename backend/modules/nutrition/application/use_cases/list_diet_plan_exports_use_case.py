from backend.modules.nutrition.application.dto.diet_plan_export_dto import (
    DietPlanExportResult,
    ListDietPlanExportsQuery,
)
from backend.modules.nutrition.application.use_cases.exceptions import DietPlanNotFoundError
from backend.modules.nutrition.domain import DietPlanExportRepository, DietPlanRepository


class ListDietPlanExportsUseCase:
    def __init__(
        self,
        diet_plan_repository: DietPlanRepository,
        diet_plan_export_repository: DietPlanExportRepository,
    ) -> None:
        self._diet_plan_repository = diet_plan_repository
        self._diet_plan_export_repository = diet_plan_export_repository

    async def execute(self, query: ListDietPlanExportsQuery) -> list[DietPlanExportResult]:
        plan = await self._diet_plan_repository.get_by_id(query.plan_id)
        if plan is None or plan.user_id != query.user_id:
            raise DietPlanNotFoundError("Diet plan not found.")

        exports = await self._diet_plan_export_repository.list_by_diet_plan_id(query.plan_id)
        return [DietPlanExportResult.from_domain(export) for export in exports]
