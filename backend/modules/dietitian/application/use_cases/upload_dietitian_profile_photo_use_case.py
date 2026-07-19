from uuid import UUID

from backend.modules.dietitian.application.dto.dietitian_profile_dto import DietitianProfileResult
from backend.modules.dietitian.application.ports.file_storage import FileStorage
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.domain.entities.dietitian_profile import MAX_PROFILE_PHOTOS
from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    PhotoLimitExceededError,
)
from backend.modules.dietitian.domain.repositories.dietitian_profile_repository import (
    DietitianProfileRepository,
)


class UploadDietitianProfilePhotoUseCase:
    def __init__(
        self,
        profile_repository: DietitianProfileRepository,
        file_storage: FileStorage,
    ) -> None:
        self._profile_repository = profile_repository
        self._file_storage = file_storage

    async def execute(self, user_id: UUID, filename: str, content: bytes) -> DietitianProfileResult:
        profile = await self._profile_repository.get_by_user_id(user_id)
        if profile is None:
            raise DietitianProfileNotFoundError("No dietitian profile found for this user.")

        # Checked here, before writing anything to disk — add_photo() enforces
        # the same cap, but only after the file would already be written.
        if len(profile.photos) >= MAX_PROFILE_PHOTOS:
            raise PhotoLimitExceededError(
                f"A dietitian profile can have at most {MAX_PROFILE_PHOTOS} photos."
            )

        photo_url = await self._file_storage.save(filename, content)
        profile.add_photo(photo_url)
        await self._profile_repository.save(profile)

        return DietitianProfileResult.from_domain(profile)
