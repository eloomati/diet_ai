from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.dietitian.application.ports.file_storage import FileStorage
from backend.modules.dietitian.application.use_cases.get_my_dietitian_application_use_case import (
    GetMyDietitianApplicationUseCase,
)
from backend.modules.dietitian.application.use_cases.get_my_dietitian_profile_use_case import (
    GetMyDietitianProfileUseCase,
)
from backend.modules.dietitian.application.use_cases.remove_dietitian_profile_photo_use_case import (
    RemoveDietitianProfilePhotoUseCase,
)
from backend.modules.dietitian.application.use_cases.submit_dietitian_application_use_case import (
    SubmitDietitianApplicationUseCase,
)
from backend.modules.dietitian.application.use_cases.update_dietitian_profile_use_case import (
    UpdateDietitianProfileUseCase,
)
from backend.modules.dietitian.application.use_cases.upload_dietitian_profile_photo_use_case import (
    UploadDietitianProfilePhotoUseCase,
)
from backend.modules.dietitian.domain.repositories.dietitian_application_repository import (
    DietitianApplicationRepository,
)
from backend.modules.dietitian.domain.repositories.dietitian_profile_repository import (
    DietitianProfileRepository,
)
from backend.modules.dietitian.infrastructure.persistence.repository.sqlalchemy_dietitian_application_repository import (
    SqlAlchemyDietitianApplicationRepository,
)
from backend.modules.dietitian.infrastructure.persistence.repository.sqlalchemy_dietitian_profile_repository import (
    SqlAlchemyDietitianProfileRepository,
)
from backend.modules.dietitian.infrastructure.storage.local_disk_file_storage import (
    LocalDiskFileStorage,
)
from backend.shared.config import get_settings
from backend.shared.database import get_db_session


def get_dietitian_application_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DietitianApplicationRepository:
    return SqlAlchemyDietitianApplicationRepository(session)


def get_submit_dietitian_application_use_case(
    repository: DietitianApplicationRepository = Depends(get_dietitian_application_repository),
) -> SubmitDietitianApplicationUseCase:
    return SubmitDietitianApplicationUseCase(repository)


def get_my_dietitian_application_use_case(
    repository: DietitianApplicationRepository = Depends(get_dietitian_application_repository),
) -> GetMyDietitianApplicationUseCase:
    return GetMyDietitianApplicationUseCase(repository)


def get_dietitian_profile_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DietitianProfileRepository:
    return SqlAlchemyDietitianProfileRepository(session)


def get_file_storage() -> FileStorage:
    settings = get_settings()
    return LocalDiskFileStorage(
        base_dir=settings.dietitian_photos_storage_dir,
        base_url=settings.dietitian_photos_base_url,
    )


def get_upload_dietitian_profile_photo_use_case(
    profile_repository: DietitianProfileRepository = Depends(get_dietitian_profile_repository),
    file_storage: FileStorage = Depends(get_file_storage),
) -> UploadDietitianProfilePhotoUseCase:
    return UploadDietitianProfilePhotoUseCase(profile_repository, file_storage)


def get_my_dietitian_profile_use_case(
    repository: DietitianProfileRepository = Depends(get_dietitian_profile_repository),
) -> GetMyDietitianProfileUseCase:
    return GetMyDietitianProfileUseCase(repository)


def get_update_dietitian_profile_use_case(
    repository: DietitianProfileRepository = Depends(get_dietitian_profile_repository),
) -> UpdateDietitianProfileUseCase:
    return UpdateDietitianProfileUseCase(repository)


def get_remove_dietitian_profile_photo_use_case(
    repository: DietitianProfileRepository = Depends(get_dietitian_profile_repository),
) -> RemoveDietitianProfilePhotoUseCase:
    return RemoveDietitianProfilePhotoUseCase(repository)
