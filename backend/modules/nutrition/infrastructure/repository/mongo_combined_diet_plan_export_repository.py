from uuid import UUID

from backend.modules.nutrition.domain.entities.combined_diet_plan_export import (
    CombinedDietPlanExport,
)
from backend.modules.nutrition.domain.repositories.combined_diet_plan_export_repository import (
    CombinedDietPlanExportRepository,
)
from backend.modules.nutrition.infrastructure.documents.combined_diet_plan_export_document import (
    CombinedDietPlanExportDocument,
)
from backend.modules.nutrition.infrastructure.mappers.combined_diet_plan_export_mapper import (
    CombinedDietPlanExportMapper,
)


class MongoCombinedDietPlanExportRepository(CombinedDietPlanExportRepository):
    async def save(self, export: CombinedDietPlanExport) -> None:
        document = CombinedDietPlanExportMapper.to_document(export)
        await document.save()

    async def get_by_id(self, export_id: UUID) -> CombinedDietPlanExport | None:
        document = await CombinedDietPlanExportDocument.get(export_id)
        return CombinedDietPlanExportMapper.to_domain(document) if document else None

    async def delete_by_user_id(self, user_id: UUID) -> None:
        await CombinedDietPlanExportDocument.find(
            CombinedDietPlanExportDocument.user_id == user_id
        ).delete()
