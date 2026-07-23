from uuid import uuid4

import pytest

from backend.modules.admin.application.use_cases.delete_user_use_case import DeleteUserUseCase
from backend.modules.admin.application.use_cases.exceptions import CannotDeleteSelfError
from backend.modules.conversation.domain import Conversation, ConversationCategory
from backend.modules.conversation.tests.fakes import InMemoryConversationRepository
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.tests.fakes import InMemoryUserRepository
from backend.modules.nutrition.domain import (
    ActivityLevel,
    CombinedDietPlanExport,
    DietDay,
    DietGoal,
    DietPlan,
    DietPlanExport,
    DietType,
    Meal,
    NutritionProfile,
)
from backend.modules.nutrition.tests.fakes import (
    InMemoryCombinedDietPlanExportRepository,
    InMemoryDietPlanExportRepository,
    InMemoryDietPlanRepository,
    InMemoryNutritionProfileRepository,
)


def _build_use_case():
    user_repo = InMemoryUserRepository()
    conversation_repo = InMemoryConversationRepository()
    nutrition_profile_repo = InMemoryNutritionProfileRepository()
    diet_plan_repo = InMemoryDietPlanRepository()
    diet_plan_export_repo = InMemoryDietPlanExportRepository()
    combined_diet_plan_export_repo = InMemoryCombinedDietPlanExportRepository()
    use_case = DeleteUserUseCase(
        user_repo,
        conversation_repo,
        nutrition_profile_repo,
        diet_plan_repo,
        diet_plan_export_repo,
        combined_diet_plan_export_repo,
    )
    return (
        use_case,
        user_repo,
        conversation_repo,
        nutrition_profile_repo,
        diet_plan_repo,
        diet_plan_export_repo,
        combined_diet_plan_export_repo,
    )


@pytest.mark.asyncio
async def test_delete_user_removes_the_user_and_all_cross_database_data() -> None:
    (
        use_case,
        user_repo,
        conversation_repo,
        nutrition_profile_repo,
        diet_plan_repo,
        diet_plan_export_repo,
        combined_diet_plan_export_repo,
    ) = _build_use_case()

    user = User.create(email=Email("todelete@example.com"), password_hash=PasswordHash("$2b$12$" + "a" * 22))
    await user_repo.save(user)

    conversation = Conversation.create(
        user_id=user.id, title="Chat", categories=[ConversationCategory.GENERAL]
    )
    await conversation_repo.save(conversation)

    profile = NutritionProfile.create(
        user_id=user.id,
        age=30,
        height_cm=180,
        weight_kg=80,
        activity_level=ActivityLevel.MODERATE,
        goal=DietGoal.MAINTENANCE,
        diet_type=DietType.STANDARD,
    )
    await nutrition_profile_repo.save(profile)

    plan = DietPlan.create(
        user_id=user.id,
        goal=DietGoal.MAINTENANCE,
        diet_type=DietType.STANDARD,
        duration_days=1,
        days=(DietDay(day_number=1, meals=(Meal(name="Oatmeal", calories=400, protein=20, carbohydrates=60, fat=10),)),),
    )
    await diet_plan_repo.save(plan)

    export = DietPlanExport.create(user_id=user.id, diet_plan_id=plan.id, filename="plan.csv")
    await diet_plan_export_repo.save(export)

    combined_export = CombinedDietPlanExport.create(
        user_id=user.id, diet_plan_ids=(plan.id,), filename="combined.csv"
    )
    await combined_diet_plan_export_repo.save(combined_export)

    other_user_id = uuid4()

    await use_case.execute(user.id, caller_id=other_user_id)

    assert await user_repo.get_by_id(user.id) is None
    assert await conversation_repo.list_by_user(user.id) == []
    assert await nutrition_profile_repo.get_by_user_id(user.id) is None
    assert await diet_plan_repo.list_by_user_id(user.id) == []
    assert await diet_plan_export_repo.list_by_diet_plan_id(plan.id) == []
    assert await combined_diet_plan_export_repo.get_by_id(combined_export.id) is None


@pytest.mark.asyncio
async def test_delete_user_raises_when_missing() -> None:
    use_case, *_ = _build_use_case()

    with pytest.raises(UserNotFoundError):
        await use_case.execute(uuid4(), caller_id=uuid4())


@pytest.mark.asyncio
async def test_delete_user_rejects_deleting_self() -> None:
    use_case, user_repo, *_ = _build_use_case()
    user = User.create(email=Email("self@example.com"), password_hash=PasswordHash("$2b$12$" + "a" * 22))
    await user_repo.save(user)

    with pytest.raises(CannotDeleteSelfError):
        await use_case.execute(user.id, caller_id=user.id)

    assert await user_repo.get_by_id(user.id) is not None
