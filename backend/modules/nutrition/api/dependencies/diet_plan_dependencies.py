from fastapi import Depends

from backend.modules.ai.domain import LLMProvider
from backend.modules.ai.infrastructure.provider_factory import get_llm_provider
from backend.modules.nutrition.api.dependencies.nutrition_dependencies import (
    get_nutrition_profile_repository,
)
from backend.modules.nutrition.application import (
    DownloadDietPlanExportUseCase,
    ExportDietPlanUseCase,
    GenerateDietPlanUseCase,
    GetDietPlanUseCase,
    ListDietPlanExportsUseCase,
    ListDietPlansUseCase,
    RescheduleMealUseCase,
)
from backend.modules.nutrition.application.ports.sftp_client import SftpClient
from backend.modules.nutrition.domain import (
    DietPlanExportRepository,
    DietPlanRepository,
    NutritionProfileRepository,
)
from backend.modules.nutrition.infrastructure.repository.mongo_diet_plan_export_repository import (
    MongoDietPlanExportRepository,
)
from backend.modules.nutrition.infrastructure.repository.mongo_diet_plan_repository import (
    MongoDietPlanRepository,
)
from backend.modules.nutrition.infrastructure.sftp.sftp_client_factory import build_sftp_client
from backend.shared.config import get_settings


def get_diet_plan_repository() -> DietPlanRepository:
    return MongoDietPlanRepository()


def get_diet_plan_export_repository() -> DietPlanExportRepository:
    return MongoDietPlanExportRepository()


def get_sftp_client() -> SftpClient:
    settings = get_settings()
    return build_sftp_client(settings)


def get_generate_diet_plan_use_case(
    diet_plan_repository: DietPlanRepository = Depends(get_diet_plan_repository),
    nutrition_profile_repository: NutritionProfileRepository = Depends(get_nutrition_profile_repository),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> GenerateDietPlanUseCase:
    return GenerateDietPlanUseCase(diet_plan_repository, nutrition_profile_repository, llm_provider)


def get_list_diet_plans_use_case(
    repository: DietPlanRepository = Depends(get_diet_plan_repository),
) -> ListDietPlansUseCase:
    return ListDietPlansUseCase(repository)


def get_diet_plan_use_case(
    repository: DietPlanRepository = Depends(get_diet_plan_repository),
) -> GetDietPlanUseCase:
    return GetDietPlanUseCase(repository)


def get_reschedule_meal_use_case(
    repository: DietPlanRepository = Depends(get_diet_plan_repository),
) -> RescheduleMealUseCase:
    return RescheduleMealUseCase(repository)


def get_export_diet_plan_use_case(
    diet_plan_repository: DietPlanRepository = Depends(get_diet_plan_repository),
    diet_plan_export_repository: DietPlanExportRepository = Depends(get_diet_plan_export_repository),
    sftp_client: SftpClient = Depends(get_sftp_client),
) -> ExportDietPlanUseCase:
    return ExportDietPlanUseCase(diet_plan_repository, diet_plan_export_repository, sftp_client)


def get_list_diet_plan_exports_use_case(
    diet_plan_repository: DietPlanRepository = Depends(get_diet_plan_repository),
    diet_plan_export_repository: DietPlanExportRepository = Depends(get_diet_plan_export_repository),
) -> ListDietPlanExportsUseCase:
    return ListDietPlanExportsUseCase(diet_plan_repository, diet_plan_export_repository)


def get_download_diet_plan_export_use_case(
    diet_plan_export_repository: DietPlanExportRepository = Depends(get_diet_plan_export_repository),
    sftp_client: SftpClient = Depends(get_sftp_client),
) -> DownloadDietPlanExportUseCase:
    return DownloadDietPlanExportUseCase(diet_plan_export_repository, sftp_client)
