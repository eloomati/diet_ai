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


class GetMyDietitianApplicationUseCase:
    def __init__(self, repository: DietitianApplicationRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: UUID) -> DietitianApplicationResult:
        application = await self._repository.get_by_user_id(user_id)
        if application is None:
            raise DietitianApplicationNotFoundError("No dietitian application found.")

        return DietitianApplicationResult.from_domain(application)
