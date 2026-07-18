from fastapi import Depends

from backend.modules.ai.domain import LLMProvider
from backend.modules.ai.infrastructure.provider_factory import get_llm_provider
from backend.modules.nutrition.api.dependencies.nutrition_dependencies import (
    get_nutrition_profile_repository,
)
from backend.modules.nutrition.application import (
    GenerateDietPlanUseCase,
    GetDietPlanUseCase,
    ListDietPlansUseCase,
    RescheduleMealUseCase,
)
from backend.modules.nutrition.domain import DietPlanRepository, NutritionProfileRepository
from backend.modules.nutrition.infrastructure.repository.mongo_diet_plan_repository import (
    MongoDietPlanRepository,
)


def get_diet_plan_repository() -> DietPlanRepository:
    return MongoDietPlanRepository()


def get_generate_diet_plan_use_case(
    diet_plan_repository: DietPlanRepository = Depends(get_diet_plan_repository),
    nutrition_profile_repository: NutritionProfileRepository = Depends(get_nutrition_profile_repository),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> GenerateDietPlanUseCase:
    return GenerateDietPlanUseCase(diet_plan_repository, nutrition_profile_repository, llm_provider)


def get_list_diet_plans_use_case(
    repository: DietPlanRepository = Depends(get_diet_plan_repository),
) -> ListDietPlansUseCase:
    return ListDietPlansUseCase(repository)


def get_diet_plan_use_case(
    repository: DietPlanRepository = Depends(get_diet_plan_repository),
) -> GetDietPlanUseCase:
    return GetDietPlanUseCase(repository)


def get_reschedule_meal_use_case(
    repository: DietPlanRepository = Depends(get_diet_plan_repository),
) -> RescheduleMealUseCase:
    return RescheduleMealUseCase(repository)
