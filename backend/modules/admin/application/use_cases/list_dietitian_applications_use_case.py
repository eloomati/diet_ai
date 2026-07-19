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
        self, status: ApplicationStatus | None = None
    ) -> list[DietitianApplicationResult]:
        applications = await self._application_repository.list_all(status)
        return [DietitianApplicationResult.from_domain(a) for a in applications]
