from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    InvalidDietitianProfileError,
    PhotoLimitExceededError,
)
from backend.shared.validation import is_valid_human_name

MAX_PROFILE_PHOTOS = 3


@dataclass(slots=True)
class DietitianProfile:
    id: UUID
    user_id: UUID
    experience: str
    diplomas: tuple[str, ...]
    description: str
    photos: tuple[str, ...] = ()
    # Both optional and independent of each other/of `display_name` — a
    # dietitian filling these in is itself the choice to show a real name
    # publicly instead of their generic `display_name`/email (Phase 13).
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        user_id: UUID,
        experience: str,
        diplomas: tuple[str, ...],
        description: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> "DietitianProfile":
        cls._validate(experience, description, first_name, last_name)
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            user_id=user_id,
            experience=experience,
            diplomas=diplomas,
            description=description,
            first_name=first_name,
            last_name=last_name,
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
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> None:
        # `None` means "leave unchanged" for first_name/last_name too, same
        # as experience/description above — there's currently no way to
        # explicitly clear a name back to unset once set, matching this
        # method's existing convention rather than inventing a separate
        # sentinel for it.
        new_experience = experience if experience is not None else self.experience
        new_description = description if description is not None else self.description
        new_first_name = first_name if first_name is not None else self.first_name
        new_last_name = last_name if last_name is not None else self.last_name
        self._validate(new_experience, new_description, new_first_name, new_last_name)

        self.experience = new_experience
        self.description = new_description
        self.first_name = new_first_name
        self.last_name = new_last_name
        if diplomas is not None:
            self.diplomas = diplomas
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _validate(
        experience: str,
        description: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> None:
        if not experience.strip():
            raise InvalidDietitianProfileError("Experience cannot be empty.")
        if not description.strip():
            raise InvalidDietitianProfileError("Description cannot be empty.")
        if first_name is not None and not is_valid_human_name(first_name):
            raise InvalidDietitianProfileError(
                "First name must contain only letters, digits, and single spaces between them."
            )
        if last_name is not None and not is_valid_human_name(last_name):
            raise InvalidDietitianProfileError(
                "Last name must contain only letters, digits, and single spaces between them."
            )
