from uuid import uuid4

import pytest

from backend.modules.dietitian.application.dto.dietitian_profile_dto import (
    UpdateDietitianProfileCommand,
)
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.application.use_cases.update_dietitian_profile_use_case import (
    UpdateDietitianProfileUseCase,
)
from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    InvalidDietitianProfileError,
)
from backend.modules.dietitian.tests.fakes import InMemoryDietitianProfileRepository


@pytest.mark.asyncio
async def test_update_profile_changes_only_given_fields() -> None:
    repo = InMemoryDietitianProfileRepository()
    user_id = uuid4()
    profile = DietitianProfile.create(
        user_id=user_id,
        experience="5 years experience",
        diplomas=("MSc Dietetics",),
        description="Weight management specialist.",
    )
    await repo.save(profile)
    use_case = UpdateDietitianProfileUseCase(repo)

    result = await use_case.execute(
        UpdateDietitianProfileCommand(user_id=user_id, description="Updated description.")
    )

    assert result.description == "Updated description."
    assert result.experience == "5 years experience"


@pytest.mark.asyncio
async def test_update_profile_raises_when_absent() -> None:
    repo = InMemoryDietitianProfileRepository()
    use_case = UpdateDietitianProfileUseCase(repo)

    with pytest.raises(DietitianProfileNotFoundError):
        await use_case.execute(UpdateDietitianProfileCommand(user_id=uuid4(), description="x"))


@pytest.mark.asyncio
async def test_update_profile_rejects_blanking_out_experience() -> None:
    repo = InMemoryDietitianProfileRepository()
    user_id = uuid4()
    await repo.save(
        DietitianProfile.create(
            user_id=user_id,
            experience="5 years experience",
            diplomas=(),
            description="desc",
        )
    )
    use_case = UpdateDietitianProfileUseCase(repo)

    with pytest.raises(InvalidDietitianProfileError):
        await use_case.execute(UpdateDietitianProfileCommand(user_id=user_id, experience="   "))
