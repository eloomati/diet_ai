from pydantic import BaseModel

from backend.modules.nutrition.application.dto.diet_plan_export_dto import DietPlanExportResult


class DietPlanExportResponse(BaseModel):
    export_id: str
    diet_plan_id: str
    filename: str
    created_at: str

    @classmethod
    def from_result(cls, result: DietPlanExportResult) -> "DietPlanExportResponse":
        return cls(
            export_id=result.export_id,
            diet_plan_id=result.diet_plan_id,
            filename=result.filename,
            created_at=result.created_at,
        )
