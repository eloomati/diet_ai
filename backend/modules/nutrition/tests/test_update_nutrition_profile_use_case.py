from uuid import uuid4

import pytest

from backend.modules.nutrition.application import (
    CreateNutritionProfileCommand,
    CreateNutritionProfileUseCase,
    NutritionProfileNotFoundError,
    UpdateNutritionProfileCommand,
    UpdateNutritionProfileUseCase,
)
from backend.modules.nutrition.tests.fakes import InMemoryNutritionProfileRepository


@pytest.mark.asyncio
async def test_update_nutrition_profile_changes_only_provided_fields() -> None:
    repo = InMemoryNutritionProfileRepository()
    user_id = uuid4()
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

    result = await UpdateNutritionProfileUseCase(repo).execute(
        UpdateNutritionProfileCommand(user_id=user_id, weight_kg=82, activity_level="VERY_HIGH")
    )

    assert result.weight_kg == 82
    assert result.activity_level == "VERY_HIGH"
    assert result.age == 29
    assert result.diet_type == "VEGETARIAN"


@pytest.mark.asyncio
async def test_update_nutrition_profile_raises_when_missing() -> None:
    repo = InMemoryNutritionProfileRepository()

    with pytest.raises(NutritionProfileNotFoundError):
        await UpdateNutritionProfileUseCase(repo).execute(
            UpdateNutritionProfileCommand(user_id=uuid4(), weight_kg=82)
        )
