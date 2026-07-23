from uuid import uuid4

import pytest

from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianApplicationNotFoundError,
)
from backend.modules.dietitian.application.use_cases.get_my_dietitian_application_use_case import (
    GetMyDietitianApplicationUseCase,
)
from backend.modules.dietitian.domain.entities.dietitian_application import DietitianApplication
from backend.modules.dietitian.tests.fakes import InMemoryDietitianApplicationRepository


@pytest.mark.asyncio
async def test_get_my_application_returns_result_when_present() -> None:
    repo = InMemoryDietitianApplicationRepository()
    user_id = uuid4()
    application = DietitianApplication.create(
        user_id=user_id,
        experience="5 years experience",
        diplomas=("MSc Dietetics",),
        description="Weight management specialist.",
    )
    await repo.save(application)
    use_case = GetMyDietitianApplicationUseCase(repo)

    result = await use_case.execute(user_id)

    assert result.user_id == user_id
    assert result.status == "PENDING"


@pytest.mark.asyncio
async def test_get_my_application_raises_when_absent() -> None:
    repo = InMemoryDietitianApplicationRepository()
    use_case = GetMyDietitianApplicationUseCase(repo)

    with pytest.raises(DietitianApplicationNotFoundError):
        await use_case.execute(uuid4())
