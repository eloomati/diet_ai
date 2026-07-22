from uuid import uuid4

from backend.modules.nutrition.application.csv_export import build_combined_diet_plan_csv
from backend.modules.nutrition.application.dto.diet_plan_dto import DietPlanResult
from backend.modules.nutrition.application.dto.diet_plan_export_dto import (
    CombinedDietPlanExportResult,
    ExportCombinedDietPlansCommand,
)
from backend.modules.nutrition.application.ports.sftp_client import SftpClient
from backend.modules.nutrition.application.use_cases.exceptions import DietPlanNotFoundError
from backend.modules.nutrition.domain import CombinedDietPlanExport, CombinedDietPlanExportRepository, DietPlanRepository


class ExportCombinedDietPlansUseCase:
    """Archives the combined CSV to SFTP and records it, mirroring
    `ExportDietPlanUseCase`'s single-plan behavior — "save" only, no
    immediate download. A separate download call (see
    `DownloadCombinedDietPlanExportUseCase`) retrieves the content later."""

    def __init__(
        self,
        diet_plan_repository: DietPlanRepository,
        combined_diet_plan_export_repository: CombinedDietPlanExportRepository,
        sftp_client: SftpClient,
    ) -> None:
        self._diet_plan_repository = diet_plan_repository
        self._combined_diet_plan_export_repository = combined_diet_plan_export_repository
        self._sftp_client = sftp_client

    async def execute(self, command: ExportCombinedDietPlansCommand) -> CombinedDietPlanExportResult:
        results = []
        for plan_id in command.plan_ids:
            plan = await self._diet_plan_repository.get_by_id(plan_id)
            if plan is None or plan.user_id != command.user_id:
                raise DietPlanNotFoundError("Diet plan not found.")
            results.append(DietPlanResult.from_domain(plan))

        csv_content = build_combined_diet_plan_csv(results)
        filename = f"combined-diet-plans-{uuid4().hex[:8]}.csv"
        await self._sftp_client.upload(filename, csv_content.encode("utf-8"))

        export = CombinedDietPlanExport.create(
            user_id=command.user_id, diet_plan_ids=command.plan_ids, filename=filename
        )
        await self._combined_diet_plan_export_repository.save(export)

        return CombinedDietPlanExportResult.from_domain(export)
