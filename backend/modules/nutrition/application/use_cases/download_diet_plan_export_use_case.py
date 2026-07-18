from backend.modules.nutrition.application.dto.diet_plan_export_dto import (
    DietPlanExportContent,
    DownloadDietPlanExportQuery,
)
from backend.modules.nutrition.application.ports.sftp_client import SftpClient
from backend.modules.nutrition.application.use_cases.exceptions import (
    DietPlanExportNotFoundError,
)
from backend.modules.nutrition.domain import DietPlanExportRepository


class DownloadDietPlanExportUseCase:
    def __init__(
        self,
        diet_plan_export_repository: DietPlanExportRepository,
        sftp_client: SftpClient,
    ) -> None:
        self._diet_plan_export_repository = diet_plan_export_repository
        self._sftp_client = sftp_client

    async def execute(self, query: DownloadDietPlanExportQuery) -> DietPlanExportContent:
        export = await self._diet_plan_export_repository.get_by_id(query.export_id)
        if (
            export is None
            or export.user_id != query.user_id
            or export.diet_plan_id != query.plan_id
        ):
            raise DietPlanExportNotFoundError("Diet plan export not found.")

        content = await self._sftp_client.download(export.filename)
        return DietPlanExportContent(filename=export.filename, content=content)
