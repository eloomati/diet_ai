from uuid import UUID

from backend.modules.admin.application.dto.admin_dto import UserSummaryResult
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain.repositories.user_repository import UserRepository


class ActivateUserUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, user_id: UUID) -> UserSummaryResult:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError("User not found.")

        user.activate()
        await self._user_repository.save(user)

        return UserSummaryResult.from_domain(user)
