from uuid import uuid4

from backend.modules.nutrition.application.csv_export import build_diet_plan_csv
from backend.modules.nutrition.application.dto.diet_plan_dto import DietPlanResult
from backend.modules.nutrition.application.dto.diet_plan_export_dto import (
    DietPlanExportResult,
    ExportDietPlanCommand,
)
from backend.modules.nutrition.application.ports.sftp_client import SftpClient
from backend.modules.nutrition.application.use_cases.exceptions import DietPlanNotFoundError
from backend.modules.nutrition.domain import DietPlanExport, DietPlanExportRepository, DietPlanRepository


class ExportDietPlanUseCase:
    def __init__(
        self,
        diet_plan_repository: DietPlanRepository,
        diet_plan_export_repository: DietPlanExportRepository,
        sftp_client: SftpClient,
    ) -> None:
        self._diet_plan_repository = diet_plan_repository
        self._diet_plan_export_repository = diet_plan_export_repository
        self._sftp_client = sftp_client

    async def execute(self, command: ExportDietPlanCommand) -> DietPlanExportResult:
        plan = await self._diet_plan_repository.get_by_id(command.plan_id)
        if plan is None or plan.user_id != command.user_id:
            raise DietPlanNotFoundError("Diet plan not found.")

        csv_content = build_diet_plan_csv(DietPlanResult.from_domain(plan))
        # Unique per export, not per plan — a plan can be exported more than once
        # (e.g. after rescheduling a meal), and each export is its own archived file.
        filename = f"{plan.id}-{uuid4().hex[:8]}.csv"
        await self._sftp_client.upload(filename, csv_content.encode("utf-8"))

        export = DietPlanExport.create(user_id=command.user_id, diet_plan_id=plan.id, filename=filename)
        await self._diet_plan_export_repository.save(export)

        return DietPlanExportResult.from_domain(export)
