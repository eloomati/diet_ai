from backend.modules.nutrition.application.dto.nutrition_profile_dto import (
    GetNutritionProfileQuery,
    NutritionProfileResult,
)
from backend.modules.nutrition.application.use_cases.exceptions import (
    NutritionProfileNotFoundError,
)
from backend.modules.nutrition.domain import NutritionProfileRepository


class GetNutritionProfileUseCase:
    def __init__(self, repository: NutritionProfileRepository) -> None:
        self._repository = repository

    async def execute(self, query: GetNutritionProfileQuery) -> NutritionProfileResult:
        profile = await self._repository.get_by_user_id(query.user_id)
        if profile is None:
            raise NutritionProfileNotFoundError("Nutrition profile not found.")

        return NutritionProfileResult.from_domain(profile)
