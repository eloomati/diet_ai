from backend.modules.dietitian.application.dto.dietitian_application_dto import (
    DietitianApplicationResult,
    SubmitDietitianApplicationCommand,
)
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianApplicationAlreadyExistsError,
)
from backend.modules.dietitian.domain.entities.dietitian_application import DietitianApplication
from backend.modules.dietitian.domain.repositories.dietitian_application_repository import (
    DietitianApplicationRepository,
)


class SubmitDietitianApplicationUseCase:
    def __init__(self, repository: DietitianApplicationRepository) -> None:
        self._repository = repository

    async def execute(self, command: SubmitDietitianApplicationCommand) -> DietitianApplicationResult:
        existing = await self._repository.get_by_user_id(command.user_id)
        if existing is not None:
            raise DietitianApplicationAlreadyExistsError(
                "You have already submitted a dietitian application."
            )

        application = DietitianApplication.create(
            user_id=command.user_id,
            experience=command.experience,
            diplomas=command.diplomas,
            description=command.description,
        )
        await self._repository.save(application)

        return DietitianApplicationResult.from_domain(application)
