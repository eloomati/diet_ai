from backend.modules.nutrition.application.dto.nutrition_profile_dto import (
    NutritionProfileResult,
    UpdateNutritionProfileCommand,
)
from backend.modules.nutrition.application.use_cases.exceptions import (
    NutritionProfileNotFoundError,
)
from backend.modules.nutrition.domain import (
    ActivityLevel,
    DietGoal,
    DietType,
    NutritionProfileRepository,
)


class UpdateNutritionProfileUseCase:
    def __init__(self, repository: NutritionProfileRepository) -> None:
        self._repository = repository

    async def execute(self, command: UpdateNutritionProfileCommand) -> NutritionProfileResult:
        profile = await self._repository.get_by_user_id(command.user_id)
        if profile is None:
            raise NutritionProfileNotFoundError("Nutrition profile not found.")

        profile.update(
            age=command.age,
            height_cm=command.height_cm,
            weight_kg=command.weight_kg,
            activity_level=ActivityLevel(command.activity_level) if command.activity_level else None,
            goal=DietGoal(command.goal) if command.goal else None,
            diet_type=DietType(command.diet_type) if command.diet_type else None,
            weekly_obligations=(
                tuple(o.to_domain() for o in command.weekly_obligations)
                if command.weekly_obligations is not None
                else None
            ),
        )
        await self._repository.save(profile)

        return NutritionProfileResult.from_domain(profile)
