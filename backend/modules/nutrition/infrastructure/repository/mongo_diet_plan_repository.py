from uuid import UUID

from backend.modules.nutrition.domain.entities.diet_plan import DietPlan
from backend.modules.nutrition.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.modules.nutrition.infrastructure.documents.diet_plan_document import DietPlanDocument
from backend.modules.nutrition.infrastructure.mappers.diet_plan_mapper import DietPlanMapper


class MongoDietPlanRepository(DietPlanRepository):
    async def get_by_id(self, plan_id: UUID) -> DietPlan | None:
        document = await DietPlanDocument.get(plan_id)
        return DietPlanMapper.to_domain(document) if document else None

    async def list_by_user_id(self, user_id: UUID) -> list[DietPlan]:
        documents = (
            await DietPlanDocument.find(DietPlanDocument.user_id == user_id)
            .sort(-DietPlanDocument.created_at)
            .to_list()
        )
        return [DietPlanMapper.to_domain(document) for document in documents]

    async def save(self, plan: DietPlan) -> None:
        document = DietPlanMapper.to_document(plan)
        await document.save()
