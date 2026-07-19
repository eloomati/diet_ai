from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    InvalidDietitianProfileError,
    PhotoLimitExceededError,
)

MAX_PROFILE_PHOTOS = 3


@dataclass(slots=True)
class DietitianProfile:
    id: UUID
    user_id: UUID
    experience: str
    diplomas: tuple[str, ...]
    description: str
    photos: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        user_id: UUID,
        experience: str,
        diplomas: tuple[str, ...],
        description: str,
    ) -> "DietitianProfile":
        cls._validate(experience, description)
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            user_id=user_id,
            experience=experience,
            diplomas=diplomas,
            description=description,
            created_at=now,
            updated_at=now,
        )

    def add_photo(self, photo_url: str) -> None:
        if len(self.photos) >= MAX_PROFILE_PHOTOS:
            raise PhotoLimitExceededError(
                f"A dietitian profile can have at most {MAX_PROFILE_PHOTOS} photos."
            )
        self.photos = (*self.photos, photo_url)
        self.updated_at = datetime.now(UTC)

    def remove_photo(self, index: int) -> None:
        if index < 0 or index >= len(self.photos):
            raise InvalidDietitianProfileError(f"No photo at index {index}.")
        photos = list(self.photos)
        photos.pop(index)
        self.photos = tuple(photos)
        self.updated_at = datetime.now(UTC)

    def update_details(
        self,
        *,
        experience: str | None = None,
        diplomas: tuple[str, ...] | None = None,
        description: str | None = None,
    ) -> None:
        new_experience = experience if experience is not None else self.experience
        new_description = description if description is not None else self.description
        self._validate(new_experience, new_description)

        self.experience = new_experience
        self.description = new_description
        if diplomas is not None:
            self.diplomas = diplomas
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _validate(experience: str, description: str) -> None:
        if not experience.strip():
            raise InvalidDietitianProfileError("Experience cannot be empty.")
        if not description.strip():
            raise InvalidDietitianProfileError("Description cannot be empty.")
