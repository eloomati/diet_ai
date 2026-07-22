from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.identity.domain.events.user_events import (
    EmailVerified,
    PasswordChanged,
    UserLoggedIn,
    UserRegistered,
    UserRoleChanged,
)
from backend.modules.identity.domain.exceptions.identity_domain_errors import (
    InactiveUserAuthenticationError,
)
from backend.modules.identity.domain.value_objects.display_name import DisplayName
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.domain.value_objects.user_status import UserStatus


@dataclass(slots=True)
class User:
    id: UUID
    email: Email
    password_hash: PasswordHash
    status: UserStatus = UserStatus.ACTIVE
    role: Role = Role.USER
    email_verified: bool = False
    # Nullable — not everyone sets one immediately; every read model falls
    # back to `email` wherever a person's identity is shown until they do.
    display_name: DisplayName | None = None
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

    def change_password(self, new_password_hash: PasswordHash) -> None:
        self.password_hash = new_password_hash
        self.updated_at = datetime.now(UTC)
        self.domain_events.append(PasswordChanged(user_id=self.id))

    def set_display_name(self, display_name: DisplayName | None) -> None:
        self.display_name = display_name
        self.updated_at = datetime.now(UTC)

    def mark_email_verified(self) -> None:
        self.email_verified = True
        self.updated_at = datetime.now(UTC)
        self.domain_events.append(EmailVerified(user_id=self.id))

    def change_role(self, new_role: Role) -> None:
        # Who is *allowed* to call this (e.g. only SUPER_ADMIN may grant
        # ADMIN/SUPER_ADMIN) is an authorization concern enforced by the
        # API layer's role-gated dependency, not a domain invariant — the
        # entity itself has no notion of "who's asking".
        self.role = new_role
        self.updated_at = datetime.now(UTC)
        self.domain_events.append(UserRoleChanged(user_id=self.id, new_role=new_role.value))