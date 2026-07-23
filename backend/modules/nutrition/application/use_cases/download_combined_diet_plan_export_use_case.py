from backend.modules.nutrition.application.dto.diet_plan_export_dto import (
    DietPlanExportContent,
    DownloadCombinedDietPlanExportQuery,
)
from backend.modules.nutrition.application.ports.sftp_client import SftpClient
from backend.modules.nutrition.application.use_cases.exceptions import DietPlanExportNotFoundError
from backend.modules.nutrition.domain import CombinedDietPlanExportRepository


class DownloadCombinedDietPlanExportUseCase:
    def __init__(
        self,
        combined_diet_plan_export_repository: CombinedDietPlanExportRepository,
        sftp_client: SftpClient,
    ) -> None:
        self._combined_diet_plan_export_repository = combined_diet_plan_export_repository
        self._sftp_client = sftp_client

    async def execute(self, query: DownloadCombinedDietPlanExportQuery) -> DietPlanExportContent:
        export = await self._combined_diet_plan_export_repository.get_by_id(query.export_id)
        if export is None or export.user_id != query.user_id:
            raise DietPlanExportNotFoundError("Combined diet plan export not found.")

        content = await self._sftp_client.download(export.filename)
        return DietPlanExportContent(filename=export.filename, content=content)
