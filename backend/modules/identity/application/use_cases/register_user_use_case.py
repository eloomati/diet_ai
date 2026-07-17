from backend.modules.identity.application.dto.register_user_dto import (
    RegisterUserCommand,
    RegisterUserResult,
)
from backend.modules.identity.application.ports.password_hasher import PasswordHasher
from backend.modules.identity.application.use_cases.exceptions import UserAlreadyExistsError
from backend.modules.identity.domain import Email, PasswordHash, PasswordPolicy, User, UserRepository


class RegisterUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    async def execute(self, command: RegisterUserCommand) -> RegisterUserResult:
        email = Email(command.email)

        exists = await self._user_repository.exists_by_email(email)
        if exists:
            raise UserAlreadyExistsError("User with this email already exists.")

        PasswordPolicy.validate(command.password)
        hashed_password = self._password_hasher.hash(command.password)

        user = User.create(
            email=email,
            password_hash=PasswordHash(hashed_password),
        )

        await self._user_repository.save(user)

        return RegisterUserResult(
            user_id=str(user.id),
            email=user.email.value,
        )