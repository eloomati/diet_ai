from backend.modules.identity.application.dto.change_user_role_dto import ChangeUserRoleCommand
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.repositories.user_repository import UserRepository


class ChangeUserRoleUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, command: ChangeUserRoleCommand) -> User:
        user = await self._user_repository.get_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError("User not found.")

        user.change_role(command.new_role)
        await self._user_repository.save(user)
        return user
