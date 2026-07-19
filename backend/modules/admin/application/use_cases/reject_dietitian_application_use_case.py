from uuid import UUID

from backend.modules.dietitian.application.dto.dietitian_application_dto import (
    DietitianApplicationResult,
)
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianApplicationNotFoundError,
)
from backend.modules.dietitian.domain.repositories.dietitian_application_repository import (
    DietitianApplicationRepository,
)


class RejectDietitianApplicationUseCase:
    def __init__(self, application_repository: DietitianApplicationRepository) -> None:
        self._application_repository = application_repository

    async def execute(self, application_id: UUID, reviewed_by: UUID) -> DietitianApplicationResult:
        application = await self._application_repository.get_by_id(application_id)
        if application is None:
            raise DietitianApplicationNotFoundError("Dietitian application not found.")

        application.reject(reviewed_by)
        await self._application_repository.save(application)

        return DietitianApplicationResult.from_domain(application)
