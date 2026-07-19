from uuid import uuid4

import pytest

from backend.modules.dietitian.application.dto.dietitian_application_dto import (
    SubmitDietitianApplicationCommand,
)
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianApplicationAlreadyExistsError,
)
from backend.modules.dietitian.application.use_cases.submit_dietitian_application_use_case import (
    SubmitDietitianApplicationUseCase,
)
from backend.modules.dietitian.tests.fakes import InMemoryDietitianApplicationRepository


def _command(**overrides) -> SubmitDietitianApplicationCommand:
    defaults = dict(
        user_id=uuid4(),
        experience="5 years as a clinical dietitian",
        diplomas=("MSc Dietetics",),
        description="Weight management specialist.",
    )
    defaults.update(overrides)
    return SubmitDietitianApplicationCommand(**defaults)


@pytest.mark.asyncio
async def test_submit_application_success() -> None:
    repo = InMemoryDietitianApplicationRepository()
    use_case = SubmitDietitianApplicationUseCase(repo)

    result = await use_case.execute(_command())

    assert result.status == "PENDING"
    assert result.experience == "5 years as a clinical dietitian"


@pytest.mark.asyncio
async def test_submit_application_rejects_duplicate_for_same_user() -> None:
    repo = InMemoryDietitianApplicationRepository()
    use_case = SubmitDietitianApplicationUseCase(repo)
    user_id = uuid4()

    await use_case.execute(_command(user_id=user_id))

    with pytest.raises(DietitianApplicationAlreadyExistsError):
        await use_case.execute(_command(user_id=user_id))


@pytest.mark.asyncio
async def test_submit_application_allows_different_users() -> None:
    repo = InMemoryDietitianApplicationRepository()
    use_case = SubmitDietitianApplicationUseCase(repo)

    await use_case.execute(_command(user_id=uuid4()))
    result = await use_case.execute(_command(user_id=uuid4()))

    assert result.status == "PENDING"
