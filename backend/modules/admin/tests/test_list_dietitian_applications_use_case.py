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

    page = await use_case.execute()

    assert {r.id for r in page.items} == {a.id, b.id}
    assert page.total == 2


@pytest.mark.asyncio
async def test_list_filters_by_status() -> None:
    repo = InMemoryDietitianApplicationRepository()
    pending = DietitianApplication.create(user_id=uuid4(), experience="exp", diplomas=(), description="d")
    approved = DietitianApplication.create(user_id=uuid4(), experience="exp2", diplomas=(), description="d2")
    approved.approve(reviewed_by=uuid4())
    await repo.save(pending)
    await repo.save(approved)
    use_case = ListDietitianApplicationsUseCase(repo)

    page = await use_case.execute(ApplicationStatus.APPROVED)

    assert [r.id for r in page.items] == [approved.id]
    assert page.total == 1


@pytest.mark.asyncio
async def test_list_applies_limit_and_offset() -> None:
    repo = InMemoryDietitianApplicationRepository()
    applications = [
        DietitianApplication.create(user_id=uuid4(), experience="exp", diplomas=(), description="d")
        for _ in range(3)
    ]
    for application in applications:
        await repo.save(application)
    use_case = ListDietitianApplicationsUseCase(repo)

    page = await use_case.execute(limit=1, offset=1)

    assert [r.id for r in page.items] == [applications[1].id]
    assert page.total == 3
