from uuid import uuid4

import pytest

from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.application.use_cases.get_my_dietitian_profile_use_case import (
    GetMyDietitianProfileUseCase,
)
from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.tests.fakes import InMemoryDietitianProfileRepository


@pytest.mark.asyncio
async def test_get_my_profile_returns_result_when_present() -> None:
    repo = InMemoryDietitianProfileRepository()
    user_id = uuid4()
    profile = DietitianProfile.create(
        user_id=user_id,
        experience="5 years experience",
        diplomas=("MSc Dietetics",),
        description="Weight management specialist.",
    )
    await repo.save(profile)
    use_case = GetMyDietitianProfileUseCase(repo)

    result = await use_case.execute(user_id)

    assert result.user_id == user_id
    assert result.experience == "5 years experience"


@pytest.mark.asyncio
async def test_get_my_profile_raises_when_absent() -> None:
    repo = InMemoryDietitianProfileRepository()
    use_case = GetMyDietitianProfileUseCase(repo)

    with pytest.raises(DietitianProfileNotFoundError):
        await use_case.execute(uuid4())
