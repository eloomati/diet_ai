from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.identity.domain.events.user_events import UserLoggedIn, UserRegistered
from backend.modules.identity.domain.exceptions.identity_domain_errors import (
    InactiveUserAuthenticationError,
)
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.domain.value_objects.user_status import UserStatus


@dataclass(slots=True)
class User:
    id: UUID
    email: Email
    password_hash: PasswordHash
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    domain_events: list[object] = field(default_factory=list)

    @classmethod
    def create(cls, email: Email, password_hash: PasswordHash) -> "User":
        now = datetime.now(UTC)
        user = cls(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        user.domain_events.append(UserRegistered(user_id=user.id, email=user.email.value))
        return user

    def can_authenticate(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def assert_can_authenticate(self) -> None:
        if not self.can_authenticate():
            raise InactiveUserAuthenticationError("Inactive or blocked users cannot authenticate.")

    def mark_logged_in(self) -> None:
        self.assert_can_authenticate()
        self.updated_at = datetime.now(UTC)
        self.domain_events.append(UserLoggedIn(user_id=self.id))

    def deactivate(self) -> None:
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.now(UTC)

    def block(self) -> None:
        self.status = UserStatus.BLOCKED
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.now(UTC)