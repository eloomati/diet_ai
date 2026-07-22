from backend.modules.nutrition.domain.entities.combined_diet_plan_export import (
    CombinedDietPlanExport,
)
from backend.modules.nutrition.infrastructure.documents.combined_diet_plan_export_document import (
    CombinedDietPlanExportDocument,
)


class CombinedDietPlanExportMapper:
    @staticmethod
    def to_domain(document: CombinedDietPlanExportDocument) -> CombinedDietPlanExport:
        return CombinedDietPlanExport(
            id=document.id,
            user_id=document.user_id,
            diet_plan_ids=tuple(document.diet_plan_ids),
            filename=document.filename,
            created_at=document.created_at,
        )

    @staticmethod
    def to_document(export: CombinedDietPlanExport) -> CombinedDietPlanExportDocument:
        return CombinedDietPlanExportDocument(
            id=export.id,
            user_id=export.user_id,
            diet_plan_ids=list(export.diet_plan_ids),
            filename=export.filename,
            created_at=export.created_at,
        )
