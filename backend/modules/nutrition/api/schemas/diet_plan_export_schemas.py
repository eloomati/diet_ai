from uuid import UUID

from pydantic import BaseModel, Field

from backend.modules.nutrition.application.dto.diet_plan_export_dto import (
    CombinedDietPlanExportResult,
    DietPlanExportResult,
)


class ExportCombinedDietPlansRequest(BaseModel):
    plan_ids: list[UUID] = Field(min_length=1)


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


class CombinedDietPlanExportResponse(BaseModel):
    export_id: str
    diet_plan_ids: list[str]
    filename: str
    created_at: str

    @classmethod
    def from_result(cls, result: CombinedDietPlanExportResult) -> "CombinedDietPlanExportResponse":
        return cls(
            export_id=result.export_id,
            diet_plan_ids=list(result.diet_plan_ids),
            filename=result.filename,
            created_at=result.created_at,
        )
