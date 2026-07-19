from uuid import UUID

from backend.modules.admin.application.use_cases.exceptions import CannotDeleteSelfError
from backend.modules.conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.nutrition.domain.repositories.diet_plan_export_repository import (
    DietPlanExportRepository,
)
from backend.modules.nutrition.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.modules.nutrition.domain.repositories.nutrition_profile_repository import (
    NutritionProfileRepository,
)


class DeleteUserUseCase:
    """Postgres's `ON DELETE CASCADE` only cleans up other Postgres tables
    (refresh tokens, dietitian applications/profiles, etc.) — it can't reach
    into Mongo, so every Mongo-held document keyed by this user's id has to
    be deleted explicitly, before the Postgres row itself, or an orphaned
    conversation/profile/plan is left behind with no owning user."""

    def __init__(
        self,
        user_repository: UserRepository,
        conversation_repository: ConversationRepository,
        nutrition_profile_repository: NutritionProfileRepository,
        diet_plan_repository: DietPlanRepository,
        diet_plan_export_repository: DietPlanExportRepository,
    ) -> None:
        self._user_repository = user_repository
        self._conversation_repository = conversation_repository
        self._nutrition_profile_repository = nutrition_profile_repository
        self._diet_plan_repository = diet_plan_repository
        self._diet_plan_export_repository = diet_plan_export_repository

    async def execute(self, user_id: UUID, caller_id: UUID) -> None:
        if user_id == caller_id:
            raise CannotDeleteSelfError("An admin cannot delete their own account.")

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError("User not found.")

        conversations = await self._conversation_repository.list_by_user(user_id)
        for conversation in conversations:
            await self._conversation_repository.delete(conversation.id)

        await self._nutrition_profile_repository.delete_by_user_id(user_id)
        await self._diet_plan_repository.delete_by_user_id(user_id)
        await self._diet_plan_export_repository.delete_by_user_id(user_id)

        await self._user_repository.delete(user_id)
