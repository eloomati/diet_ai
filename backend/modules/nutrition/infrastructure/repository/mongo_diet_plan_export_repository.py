from uuid import UUID

from backend.modules.nutrition.domain.entities.diet_plan_export import DietPlanExport
from backend.modules.nutrition.domain.repositories.diet_plan_export_repository import (
    DietPlanExportRepository,
)
from backend.modules.nutrition.infrastructure.documents.diet_plan_export_document import (
    DietPlanExportDocument,
)
from backend.modules.nutrition.infrastructure.mappers.diet_plan_export_mapper import (
    DietPlanExportMapper,
)


class MongoDietPlanExportRepository(DietPlanExportRepository):
    async def save(self, export: DietPlanExport) -> None:
        document = DietPlanExportMapper.to_document(export)
        await document.save()

    async def get_by_id(self, export_id: UUID) -> DietPlanExport | None:
        document = await DietPlanExportDocument.get(export_id)
        return DietPlanExportMapper.to_domain(document) if document else None

    async def list_by_diet_plan_id(self, diet_plan_id: UUID) -> list[DietPlanExport]:
        documents = (
            await DietPlanExportDocument.find(DietPlanExportDocument.diet_plan_id == diet_plan_id)
            .sort(-DietPlanExportDocument.created_at)
            .to_list()
        )
        return [DietPlanExportMapper.to_domain(document) for document in documents]

    async def delete_by_user_id(self, user_id: UUID) -> None:
        await DietPlanExportDocument.find(DietPlanExportDocument.user_id == user_id).delete()
