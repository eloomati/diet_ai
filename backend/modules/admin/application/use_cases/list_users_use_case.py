from backend.modules.admin.application.dto.admin_dto import UserSummaryResult
from backend.modules.admin.application.dto.pagination_dto import PageResult
from backend.modules.identity.domain.repositories.user_repository import UserRepository


class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(
        self, limit: int | None = None, offset: int = 0
    ) -> PageResult[UserSummaryResult]:
        users = await self._user_repository.list_all(limit=limit, offset=offset)
        total = await self._user_repository.count_all()
        return PageResult(
            items=[UserSummaryResult.from_domain(user) for user in users], total=total
        )
