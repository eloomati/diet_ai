from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.domain.value_objects.user_status import UserStatus
from backend.modules.identity.infrastructure.persistence.models.user_model import UserModel


class UserMapper:
    @staticmethod
    def to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            password_hash=PasswordHash(model.password_hash),
            status=UserStatus(model.status),
            role=Role(model.role),
            email_verified=model.email_verified,
            created_at=model.created_at,
            updated_at=model.updated_at,
            domain_events=[],
        )

    @staticmethod
    def to_model(user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email.value,
            password_hash=user.password_hash.value,
            status=user.status.value,
            role=user.role.value,
            email_verified=user.email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )