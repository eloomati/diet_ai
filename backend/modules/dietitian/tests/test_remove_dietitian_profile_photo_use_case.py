from uuid import uuid4

import pytest

from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.application.use_cases.remove_dietitian_profile_photo_use_case import (
    RemoveDietitianProfilePhotoUseCase,
)
from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    InvalidDietitianProfileError,
)
from backend.modules.dietitian.tests.fakes import InMemoryDietitianProfileRepository


@pytest.mark.asyncio
async def test_remove_photo_drops_it_from_the_profile() -> None:
    repo = InMemoryDietitianProfileRepository()
    user_id = uuid4()
    profile = DietitianProfile.create(
        user_id=user_id, experience="exp", diplomas=(), description="desc"
    )
    profile.add_photo("/static/dietitian-photos/a.jpg")
    profile.add_photo("/static/dietitian-photos/b.jpg")
    await repo.save(profile)
    use_case = RemoveDietitianProfilePhotoUseCase(repo)

    result = await use_case.execute(user_id, 0)

    assert result.photos == ("/static/dietitian-photos/b.jpg",)


@pytest.mark.asyncio
async def test_remove_photo_raises_when_no_profile() -> None:
    repo = InMemoryDietitianProfileRepository()
    use_case = RemoveDietitianProfilePhotoUseCase(repo)

    with pytest.raises(DietitianProfileNotFoundError):
        await use_case.execute(uuid4(), 0)


@pytest.mark.asyncio
async def test_remove_photo_raises_for_out_of_range_index() -> None:
    repo = InMemoryDietitianProfileRepository()
    user_id = uuid4()
    profile = DietitianProfile.create(
        user_id=user_id, experience="exp", diplomas=(), description="desc"
    )
    profile.add_photo("/static/dietitian-photos/a.jpg")
    await repo.save(profile)
    use_case = RemoveDietitianProfilePhotoUseCase(repo)

    with pytest.raises(InvalidDietitianProfileError):
        await use_case.execute(user_id, 5)
