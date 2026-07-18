from dataclasses import dataclass
from uuid import UUID

from backend.modules.nutrition.domain.entities.diet_plan_export import DietPlanExport


@dataclass(frozen=True, slots=True)
class ExportDietPlanCommand:
    user_id: UUID
    plan_id: UUID


@dataclass(frozen=True, slots=True)
class ListDietPlanExportsQuery:
    user_id: UUID
    plan_id: UUID


@dataclass(frozen=True, slots=True)
class DownloadDietPlanExportQuery:
    user_id: UUID
    plan_id: UUID
    export_id: UUID


@dataclass(frozen=True, slots=True)
class DietPlanExportResult:
    export_id: str
    diet_plan_id: str
    filename: str
    created_at: str

    @classmethod
    def from_domain(cls, export: DietPlanExport) -> "DietPlanExportResult":
        return cls(
            export_id=str(export.id),
            diet_plan_id=str(export.diet_plan_id),
            filename=export.filename,
            created_at=export.created_at.isoformat(),
        )


@dataclass(frozen=True, slots=True)
class DietPlanExportContent:
    filename: str
    content: bytes
