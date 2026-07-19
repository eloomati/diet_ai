from backend.modules.admin.application.dto.admin_dto import UserSummaryResult
from backend.modules.identity.domain.repositories.user_repository import UserRepository


class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self) -> list[UserSummaryResult]:
        users = await self._user_repository.list_all()
        return [UserSummaryResult.from_domain(user) for user in users]
