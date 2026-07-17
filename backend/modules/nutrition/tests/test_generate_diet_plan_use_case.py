from uuid import UUID, uuid4

import pytest

from backend.modules.ai.tests.fakes import FakeLLMProvider
from backend.modules.nutrition.application import (
    CreateNutritionProfileCommand,
    CreateNutritionProfileUseCase,
    GenerateDietPlanCommand,
    GenerateDietPlanUseCase,
    NutritionProfileNotFoundError,
)
from backend.modules.nutrition.tests.fakes import (
    InMemoryDietPlanRepository,
    InMemoryNutritionProfileRepository,
)


def _plan_dict(duration_days: int) -> dict:
    return {
        "days": [
            {
                "day_number": day,
                "meals": [
                    {
                        "name": "Oatmeal",
                        "calories": 400,
                        "protein": 20,
                        "carbohydrates": 60,
                        "fat": 10,
                    }
                ],
            }
            for day in range(1, duration_days + 1)
        ]
    }


async def _create_profile(repo: InMemoryNutritionProfileRepository, user_id) -> None:
    await CreateNutritionProfileUseCase(repo).execute(
        CreateNutritionProfileCommand(
            user_id=user_id,
            age=29,
            height_cm=187,
            weight_kg=80,
            activity_level="HIGH",
            goal="MUSCLE_GAIN",
            diet_type="VEGETARIAN",
        )
    )


@pytest.mark.asyncio
async def test_generate_diet_plan_returns_structured_plan() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(3))

    use_case = GenerateDietPlanUseCase(plan_repo, profile_repo, llm)
    result = await use_case.execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=3, requirements=("high protein",))
    )

    assert result.duration_days == 3
    assert len(result.days) == 3
    assert result.goal == "MUSCLE_GAIN"
    assert result.diet_type == "VEGETARIAN"
    assert result.requirements == ("high protein",)
    assert result.days[0].meals[0].name == "Oatmeal"


@pytest.mark.asyncio
async def test_generate_diet_plan_persists_the_plan() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(2))

    result = await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=2)
    )

    stored = await plan_repo.get_by_id(UUID(result.plan_id))
    assert stored is not None
    assert stored.user_id == user_id


@pytest.mark.asyncio
async def test_generate_diet_plan_uses_profile_in_prompt() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(1))

    await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=1)
    )

    assert llm.last_prompt is not None
    assert "MUSCLE_GAIN" in llm.last_prompt.question
    assert llm.last_schema is not None
    assert "days" in llm.last_schema["properties"]


@pytest.mark.asyncio
async def test_generate_diet_plan_without_profile_raises() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(1))

    with pytest.raises(NutritionProfileNotFoundError):
        await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
            GenerateDietPlanCommand(user_id=uuid4(), duration_days=1)
        )
