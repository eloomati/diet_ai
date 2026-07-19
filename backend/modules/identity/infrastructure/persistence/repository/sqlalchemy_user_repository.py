from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.infrastructure.mappers.user_mapper import UserMapper
from backend.modules.identity.infrastructure.persistence.models.user_model import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def get_by_email(self, email: Email) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.value)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def exists_by_email(self, email: Email) -> bool:
        stmt = select(UserModel.id).where(UserModel.email == email.value)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def save(self, user: User) -> None:
        existing = await self._session.get(UserModel, user.id)

        if existing is None:
            model = UserMapper.to_model(user)
            self._session.add(model)
        else:
            existing.email = user.email.value
            existing.password_hash = user.password_hash.value
            existing.status = user.status.value
            existing.role = user.role.value
            existing.email_verified = user.email_verified
            existing.updated_at = user.updated_at

        await self._session.flush()