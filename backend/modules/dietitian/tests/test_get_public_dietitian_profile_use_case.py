from uuid import uuid4

import pytest

from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.application.use_cases.get_public_dietitian_profile_use_case import (
    GetPublicDietitianProfileUseCase,
)
from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.domain.entities.review import Review
from backend.modules.dietitian.tests.fakes import (
    InMemoryDietitianProfileRepository,
    InMemoryReviewRepository,
)
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.tests.fakes import InMemoryUserRepository


def _password_hash() -> PasswordHash:
    return PasswordHash("$2b$12$" + "a" * 22)


async def _make_dietitian(user_repo: InMemoryUserRepository, email: str) -> User:
    dietitian = User.create(email=Email(email), password_hash=_password_hash())
    dietitian.change_role(Role.DIET_USER)
    await user_repo.save(dietitian)
    return dietitian


@pytest.mark.asyncio
async def test_get_public_profile_includes_reviews_without_reviewer_identity() -> None:
    user_repo = InMemoryUserRepository()
    profile_repo = InMemoryDietitianProfileRepository()
    review_repo = InMemoryReviewRepository()
    dietitian = await _make_dietitian(user_repo, "public@example.com")
    profile = DietitianProfile.create(
        user_id=dietitian.id,
        experience="10 years",
        diplomas=("PhD Nutrition",),
        description="Sports nutrition specialist.",
    )
    await profile_repo.save(profile)
    reviewer_id = uuid4()
    await review_repo.save(
        Review.create(
            reviewer_id=reviewer_id, dietitian_id=dietitian.id, rating=10, comment="Fantastic!"
        )
    )
    use_case = GetPublicDietitianProfileUseCase(profile_repo, user_repo, review_repo)

    result = await use_case.execute(dietitian.id)

    assert result.email == "public@example.com"
    assert result.average_rating == 10.0
    assert result.review_count == 1
    assert len(result.reviews) == 1
    assert result.reviews[0].rating == 10
    assert result.reviews[0].comment == "Fantastic!"
    assert not hasattr(result.reviews[0], "reviewer_id")


@pytest.mark.asyncio
async def test_get_public_profile_raises_when_no_profile_exists() -> None:
    use_case = GetPublicDietitianProfileUseCase(
        InMemoryDietitianProfileRepository(), InMemoryUserRepository(), InMemoryReviewRepository()
    )

    with pytest.raises(DietitianProfileNotFoundError):
        await use_case.execute(uuid4())


@pytest.mark.asyncio
async def test_get_public_profile_raises_when_dietitian_is_banned() -> None:
    user_repo = InMemoryUserRepository()
    profile_repo = InMemoryDietitianProfileRepository()
    review_repo = InMemoryReviewRepository()
    dietitian = await _make_dietitian(user_repo, "bannedpublic@example.com")
    dietitian.block()
    await user_repo.save(dietitian)
    profile = DietitianProfile.create(
        user_id=dietitian.id, experience="5 years", diplomas=(), description="Description."
    )
    await profile_repo.save(profile)
    use_case = GetPublicDietitianProfileUseCase(profile_repo, user_repo, review_repo)

    with pytest.raises(DietitianProfileNotFoundError):
        await use_case.execute(dietitian.id)
