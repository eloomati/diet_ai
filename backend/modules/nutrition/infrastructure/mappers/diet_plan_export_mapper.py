from backend.modules.nutrition.domain.entities.diet_plan_export import DietPlanExport
from backend.modules.nutrition.infrastructure.documents.diet_plan_export_document import (
    DietPlanExportDocument,
)


class DietPlanExportMapper:
    @staticmethod
    def to_domain(document: DietPlanExportDocument) -> DietPlanExport:
        return DietPlanExport(
            id=document.id,
            user_id=document.user_id,
            diet_plan_id=document.diet_plan_id,
            filename=document.filename,
            created_at=document.created_at,
        )

    @staticmethod
    def to_document(export: DietPlanExport) -> DietPlanExportDocument:
        return DietPlanExportDocument(
            id=export.id,
            user_id=export.user_id,
            diet_plan_id=export.diet_plan_id,
            filename=export.filename,
            created_at=export.created_at,
        )
