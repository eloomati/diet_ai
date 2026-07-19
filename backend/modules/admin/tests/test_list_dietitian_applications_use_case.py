from uuid import uuid4

import pytest

from backend.modules.admin.application.use_cases.list_dietitian_applications_use_case import (
    ListDietitianApplicationsUseCase,
)
from backend.modules.dietitian.domain.entities.dietitian_application import DietitianApplication
from backend.modules.dietitian.domain.value_objects.application_status import ApplicationStatus
from backend.modules.dietitian.tests.fakes import InMemoryDietitianApplicationRepository


@pytest.mark.asyncio
async def test_list_all_returns_every_application() -> None:
    repo = InMemoryDietitianApplicationRepository()
    a = DietitianApplication.create(user_id=uuid4(), experience="exp", diplomas=(), description="d")
    b = DietitianApplication.create(user_id=uuid4(), experience="exp2", diplomas=(), description="d2")
    await repo.save(a)
    await repo.save(b)
    use_case = ListDietitianApplicationsUseCase(repo)

    results = await use_case.execute()

    assert {r.id for r in results} == {a.id, b.id}


@pytest.mark.asyncio
async def test_list_filters_by_status() -> None:
    repo = InMemoryDietitianApplicationRepository()
    pending = DietitianApplication.create(user_id=uuid4(), experience="exp", diplomas=(), description="d")
    approved = DietitianApplication.create(user_id=uuid4(), experience="exp2", diplomas=(), description="d2")
    approved.approve(reviewed_by=uuid4())
    await repo.save(pending)
    await repo.save(approved)
    use_case = ListDietitianApplicationsUseCase(repo)

    results = await use_case.execute(ApplicationStatus.APPROVED)

    assert [r.id for r in results] == [approved.id]
