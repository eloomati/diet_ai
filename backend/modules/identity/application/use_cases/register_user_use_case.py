from backend.modules.identity.application.dto.register_user_dto import (
    RegisterUserCommand,
    RegisterUserResult,
)
from backend.modules.identity.application.ports.captcha_verifier import CaptchaVerifier
from backend.modules.identity.application.ports.email_sender import EmailSender
from backend.modules.identity.application.ports.password_hasher import PasswordHasher
from backend.modules.identity.application.use_cases.exceptions import (
    InvalidCaptchaError,
    UserAlreadyExistsError,
)
from backend.modules.identity.domain import (
    Email,
    EmailVerificationToken,
    EmailVerificationTokenRepository,
    PasswordHash,
    PasswordPolicy,
    User,
    UserRepository,
)

_VERIFICATION_TOKEN_TTL_MINUTES = 60 * 24


class RegisterUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        email_verification_token_repository: EmailVerificationTokenRepository,
        email_sender: EmailSender,
        captcha_verifier: CaptchaVerifier,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._email_verification_token_repository = email_verification_token_repository
        self._email_sender = email_sender
        self._captcha_verifier = captcha_verifier

    async def execute(self, command: RegisterUserCommand) -> RegisterUserResult:
        # Fail before any real work — same "check first" shape as the
        # diet-plan profile-required check.
        if not await self._captcha_verifier.verify(command.captcha_token):
            raise InvalidCaptchaError("CAPTCHA verification failed.")

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

        token, raw_token = EmailVerificationToken.issue(
            user_id=user.id, ttl_minutes=_VERIFICATION_TOKEN_TTL_MINUTES
        )
        await self._email_verification_token_repository.save(token)

        await self._email_sender.send(
            to=user.email.value,
            subject="Verify your Mycelo email address",
            body=(
                "Welcome to Mycelo! Please verify your email address.\n\n"
                f"Verification code: {raw_token}\n\n"
                f"This code expires in {_VERIFICATION_TOKEN_TTL_MINUTES // 60} hours."
            ),
            purpose="EMAIL_VERIFICATION",
        )

        return RegisterUserResult(
            user_id=str(user.id),
            email=user.email.value,
        )