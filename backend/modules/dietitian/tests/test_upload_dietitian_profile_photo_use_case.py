from uuid import uuid4

import pytest

from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.application.use_cases.upload_dietitian_profile_photo_use_case import (
    UploadDietitianProfilePhotoUseCase,
)
from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    PhotoLimitExceededError,
)
from backend.modules.dietitian.tests.fakes import FakeFileStorage, InMemoryDietitianProfileRepository


def _profile(user_id) -> DietitianProfile:
    return DietitianProfile.create(
        user_id=user_id,
        experience="5 years experience",
        diplomas=("MSc Dietetics",),
        description="Weight management specialist.",
    )


@pytest.mark.asyncio
async def test_upload_photo_appends_to_profile() -> None:
    user_id = uuid4()
    repo = InMemoryDietitianProfileRepository()
    await repo.save(_profile(user_id))
    storage = FakeFileStorage()
    use_case = UploadDietitianProfilePhotoUseCase(repo, storage)

    result = await use_case.execute(user_id, "photo.jpg", b"fake-bytes")

    assert len(result.photos) == 1
    assert storage.saved == [("photo.jpg", b"fake-bytes")]


@pytest.mark.asyncio
async def test_upload_photo_raises_when_no_profile() -> None:
    repo = InMemoryDietitianProfileRepository()
    storage = FakeFileStorage()
    use_case = UploadDietitianProfilePhotoUseCase(repo, storage)

    with pytest.raises(DietitianProfileNotFoundError):
        await use_case.execute(uuid4(), "photo.jpg", b"fake-bytes")


@pytest.mark.asyncio
async def test_upload_photo_rejects_a_fourth_without_writing_it() -> None:
    user_id = uuid4()
    profile = _profile(user_id)
    profile.add_photo("/static/dietitian-photos/a.jpg")
    profile.add_photo("/static/dietitian-photos/b.jpg")
    profile.add_photo("/static/dietitian-photos/c.jpg")
    repo = InMemoryDietitianProfileRepository()
    await repo.save(profile)
    storage = FakeFileStorage()
    use_case = UploadDietitianProfilePhotoUseCase(repo, storage)

    with pytest.raises(PhotoLimitExceededError):
        await use_case.execute(user_id, "photo.jpg", b"fake-bytes")

    assert storage.saved == []
