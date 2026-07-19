from uuid import uuid4

import pytest

from backend.modules.admin.application.use_cases.approve_dietitian_application_use_case import (
    ApproveDietitianApplicationUseCase,
)
from backend.modules.admin.application.use_cases.reject_dietitian_application_use_case import (
    RejectDietitianApplicationUseCase,
)
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianApplicationNotFoundError,
)
from backend.modules.dietitian.domain.entities.dietitian_application import DietitianApplication
from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    ApplicationAlreadyReviewedError,
)
from backend.modules.dietitian.domain.value_objects.application_status import ApplicationStatus
from backend.modules.dietitian.tests.fakes import (
    InMemoryDietitianApplicationRepository,
    InMemoryDietitianProfileRepository,
)
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.tests.fakes import InMemoryUserRepository


def _password_hash() -> PasswordHash:
    return PasswordHash("$2b$12$" + "a" * 22)


@pytest.mark.asyncio
async def test_approve_promotes_user_and_creates_profile() -> None:
    application_repo = InMemoryDietitianApplicationRepository()
    profile_repo = InMemoryDietitianProfileRepository()
    user_repo = InMemoryUserRepository()

    user = User.create(email=Email("applicant@example.com"), password_hash=_password_hash())
    await user_repo.save(user)
    application = DietitianApplication.create(
        user_id=user.id, experience="5 years", diplomas=("MSc",), description="desc"
    )
    await application_repo.save(application)

    use_case = ApproveDietitianApplicationUseCase(application_repo, profile_repo, user_repo)
    reviewer_id = uuid4()

    result = await use_case.execute(application.id, reviewed_by=reviewer_id)

    assert result.status == ApplicationStatus.APPROVED.value
    saved_user = await user_repo.get_by_id(user.id)
    assert saved_user.role == Role.DIET_USER
    profile = await profile_repo.get_by_user_id(user.id)
    assert profile is not None
    assert profile.experience == "5 years"


@pytest.mark.asyncio
async def test_approve_raises_when_application_missing() -> None:
    application_repo = InMemoryDietitianApplicationRepository()
    profile_repo = InMemoryDietitianProfileRepository()
    user_repo = InMemoryUserRepository()
    use_case = ApproveDietitianApplicationUseCase(application_repo, profile_repo, user_repo)

    with pytest.raises(DietitianApplicationNotFoundError):
        await use_case.execute(uuid4(), reviewed_by=uuid4())


@pytest.mark.asyncio
async def test_approve_raises_when_already_reviewed() -> None:
    application_repo = InMemoryDietitianApplicationRepository()
    profile_repo = InMemoryDietitianProfileRepository()
    user_repo = InMemoryUserRepository()
    user = User.create(email=Email("twice@example.com"), password_hash=_password_hash())
    await user_repo.save(user)
    application = DietitianApplication.create(
        user_id=user.id, experience="exp", diplomas=(), description="desc"
    )
    application.approve(reviewed_by=uuid4())
    await application_repo.save(application)
    use_case = ApproveDietitianApplicationUseCase(application_repo, profile_repo, user_repo)

    with pytest.raises(ApplicationAlreadyReviewedError):
        await use_case.execute(application.id, reviewed_by=uuid4())


@pytest.mark.asyncio
async def test_reject_sets_status_rejected_without_touching_role() -> None:
    application_repo = InMemoryDietitianApplicationRepository()
    user_repo = InMemoryUserRepository()
    user = User.create(email=Email("rejected@example.com"), password_hash=_password_hash())
    await user_repo.save(user)
    application = DietitianApplication.create(
        user_id=user.id, experience="exp", diplomas=(), description="desc"
    )
    await application_repo.save(application)
    use_case = RejectDietitianApplicationUseCase(application_repo)

    result = await use_case.execute(application.id, reviewed_by=uuid4())

    assert result.status == ApplicationStatus.REJECTED.value
    saved_user = await user_repo.get_by_id(user.id)
    assert saved_user.role == Role.USER


@pytest.mark.asyncio
async def test_reject_raises_when_application_missing() -> None:
    application_repo = InMemoryDietitianApplicationRepository()
    use_case = RejectDietitianApplicationUseCase(application_repo)

    with pytest.raises(DietitianApplicationNotFoundError):
        await use_case.execute(uuid4(), reviewed_by=uuid4())
