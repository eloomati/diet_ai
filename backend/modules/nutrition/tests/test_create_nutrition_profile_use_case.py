from uuid import uuid4

import pytest

from backend.modules.nutrition.application import (
    CreateNutritionProfileCommand,
    CreateNutritionProfileUseCase,
    NutritionProfileAlreadyExistsError,
)
from backend.modules.nutrition.tests.fakes import InMemoryNutritionProfileRepository


def _command(**overrides) -> CreateNutritionProfileCommand:
    defaults = dict(
        user_id=uuid4(),
        age=29,
        height_cm=187,
        weight_kg=80,
        activity_level="HIGH",
        goal="MUSCLE_GAIN",
        diet_type="VEGETARIAN",
    )
    defaults.update(overrides)
    return CreateNutritionProfileCommand(**defaults)


@pytest.mark.asyncio
async def test_create_nutrition_profile_success() -> None:
    repo = InMemoryNutritionProfileRepository()
    use_case = CreateNutritionProfileUseCase(repo)

    result = await use_case.execute(_command())

    assert result.age == 29
    assert result.activity_level == "HIGH"
    assert result.goal == "MUSCLE_GAIN"
    assert result.diet_type == "VEGETARIAN"


@pytest.mark.asyncio
async def test_create_nutrition_profile_rejects_duplicate_for_same_user() -> None:
    repo = InMemoryNutritionProfileRepository()
    use_case = CreateNutritionProfileUseCase(repo)
    user_id = uuid4()

    await use_case.execute(_command(user_id=user_id))

    with pytest.raises(NutritionProfileAlreadyExistsError):
        await use_case.execute(_command(user_id=user_id))


@pytest.mark.asyncio
async def test_create_nutrition_profile_allows_different_users() -> None:
    repo = InMemoryNutritionProfileRepository()
    use_case = CreateNutritionProfileUseCase(repo)

    await use_case.execute(_command(user_id=uuid4()))
    result = await use_case.execute(_command(user_id=uuid4()))

    assert result.age == 29
