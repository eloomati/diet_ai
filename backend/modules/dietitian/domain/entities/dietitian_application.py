from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    ApplicationAlreadyReviewedError,
    InvalidDietitianApplicationError,
)
from backend.modules.dietitian.domain.value_objects.application_status import ApplicationStatus


@dataclass(slots=True)
class DietitianApplication:
    id: UUID
    user_id: UUID
    experience: str
    diplomas: tuple[str, ...]
    description: str
    status: ApplicationStatus = ApplicationStatus.PENDING
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        user_id: UUID,
        experience: str,
        diplomas: tuple[str, ...],
        description: str,
    ) -> "DietitianApplication":
        cls._validate(experience, description)
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            user_id=user_id,
            experience=experience,
            diplomas=diplomas,
            description=description,
            status=ApplicationStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

    def approve(self, reviewed_by: UUID) -> None:
        self._assert_pending()
        self.status = ApplicationStatus.APPROVED
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.now(UTC)
        self.updated_at = self.reviewed_at

    def reject(self, reviewed_by: UUID) -> None:
        self._assert_pending()
        self.status = ApplicationStatus.REJECTED
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.now(UTC)
        self.updated_at = self.reviewed_at

    def _assert_pending(self) -> None:
        if self.status != ApplicationStatus.PENDING:
            raise ApplicationAlreadyReviewedError(
                f"Application already reviewed (status={self.status.value})."
            )

    @staticmethod
    def _validate(experience: str, description: str) -> None:
        if not experience.strip():
            raise InvalidDietitianApplicationError("Experience cannot be empty.")
        if not description.strip():
            raise InvalidDietitianApplicationError("Description cannot be empty.")
