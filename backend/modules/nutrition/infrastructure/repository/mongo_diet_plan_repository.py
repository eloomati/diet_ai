from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from backend.modules.nutrition.domain.entities.diet_plan import DietPlan
from backend.modules.nutrition.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.modules.nutrition.infrastructure.documents.diet_plan_document import DietPlanDocument
from backend.modules.nutrition.infrastructure.mappers.diet_plan_mapper import DietPlanMapper


class MongoDietPlanRepository(DietPlanRepository):
    async def get_by_id(self, plan_id: UUID) -> DietPlan | None:
        document = await DietPlanDocument.get(plan_id)
        return DietPlanMapper.to_domain(document) if document else None

    async def list_by_user_id(
        self,
        user_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[DietPlan]:
        criteria = [DietPlanDocument.user_id == user_id]
        if start_date is not None:
            criteria.append(
                DietPlanDocument.created_at >= datetime.combine(start_date, time.min, tzinfo=UTC)
            )
        if end_date is not None:
            # Exclusive upper bound at the start of the *next* day, so the whole
            # end_date calendar day is included regardless of time-of-day.
            criteria.append(
                DietPlanDocument.created_at
                < datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
            )

        documents = (
            await DietPlanDocument.find(*criteria).sort(-DietPlanDocument.created_at).to_list()
        )
        return [DietPlanMapper.to_domain(document) for document in documents]

    async def save(self, plan: DietPlan) -> None:
        document = DietPlanMapper.to_document(plan)
        await document.save()

    async def delete_by_user_id(self, user_id: UUID) -> None:
        await DietPlanDocument.find(DietPlanDocument.user_id == user_id).delete()
