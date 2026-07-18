from backend.modules.nutrition.application.dto.nutrition_profile_dto import (
    CreateNutritionProfileCommand,
    NutritionProfileResult,
)
from backend.modules.nutrition.application.use_cases.exceptions import (
    NutritionProfileAlreadyExistsError,
)
from backend.modules.nutrition.domain import (
    ActivityLevel,
    DietGoal,
    DietType,
    NutritionProfile,
    NutritionProfileRepository,
)


class CreateNutritionProfileUseCase:
    def __init__(self, repository: NutritionProfileRepository) -> None:
        self._repository = repository

    async def execute(self, command: CreateNutritionProfileCommand) -> NutritionProfileResult:
        existing = await self._repository.get_by_user_id(command.user_id)
        if existing is not None:
            raise NutritionProfileAlreadyExistsError(
                "Nutrition profile already exists for this user. Use PUT to update it."
            )

        profile = NutritionProfile.create(
            user_id=command.user_id,
            age=command.age,
            height_cm=command.height_cm,
            weight_kg=command.weight_kg,
            activity_level=ActivityLevel(command.activity_level),
            goal=DietGoal(command.goal),
            diet_type=DietType(command.diet_type),
            weekly_obligations=tuple(o.to_domain() for o in command.weekly_obligations),
        )
        await self._repository.save(profile)

        return NutritionProfileResult.from_domain(profile)
