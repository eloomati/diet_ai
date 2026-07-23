from backend.modules.admin.application.dto.pagination_dto import PageResult
from backend.modules.dietitian.application.dto.dietitian_application_dto import (
    DietitianApplicationResult,
)
from backend.modules.dietitian.domain.repositories.dietitian_application_repository import (
    DietitianApplicationRepository,
)
from backend.modules.dietitian.domain.value_objects.application_status import ApplicationStatus


class ListDietitianApplicationsUseCase:
    def __init__(self, application_repository: DietitianApplicationRepository) -> None:
        self._application_repository = application_repository

    async def execute(
        self,
        status: ApplicationStatus | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> PageResult[DietitianApplicationResult]:
        applications = await self._application_repository.list_all(
            status, limit=limit, offset=offset
        )
        total = await self._application_repository.count_all(status)
        return PageResult(
            items=[DietitianApplicationResult.from_domain(a) for a in applications],
            total=total,
        )
