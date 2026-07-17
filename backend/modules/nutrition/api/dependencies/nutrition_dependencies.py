from fastapi import Depends

from backend.modules.nutrition.application import (
    CreateNutritionProfileUseCase,
    GetNutritionProfileUseCase,
    UpdateNutritionProfileUseCase,
)
from backend.modules.nutrition.domain import NutritionProfileRepository
from backend.modules.nutrition.infrastructure.repository.mongo_nutrition_profile_repository import (
    MongoNutritionProfileRepository,
)


def get_nutrition_profile_repository() -> NutritionProfileRepository:
    return MongoNutritionProfileRepository()


def get_create_nutrition_profile_use_case(
    repository: NutritionProfileRepository = Depends(get_nutrition_profile_repository),
) -> CreateNutritionProfileUseCase:
    return CreateNutritionProfileUseCase(repository)


def get_nutrition_profile_use_case(
    repository: NutritionProfileRepository = Depends(get_nutrition_profile_repository),
) -> GetNutritionProfileUseCase:
    return GetNutritionProfileUseCase(repository)


def get_update_nutrition_profile_use_case(
    repository: NutritionProfileRepository = Depends(get_nutrition_profile_repository),
) -> UpdateNutritionProfileUseCase:
    return UpdateNutritionProfileUseCase(repository)
