from backend.modules.identity.application.dto.update_display_name_dto import (
    UpdateDisplayNameCommand,
)
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.domain.value_objects.display_name import DisplayName


class UpdateDisplayNameUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, command: UpdateDisplayNameCommand) -> User:
        user = await self._user_repository.get_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError("User not found.")

        display_name = DisplayName(command.display_name) if command.display_name else None
        user.set_display_name(display_name)
        await self._user_repository.save(user)
        return user
