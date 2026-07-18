from fastapi import APIRouter, Depends, status

from backend.shared.exceptions import AppException, ErrorCode

from backend.modules.identity.api.dependencies import (
    get_confirm_email_verification_use_case,
    get_confirm_password_reset_use_case,
    get_current_user,
    get_login_user_use_case,
    get_logout_use_case,
    get_refresh_access_token_use_case,
    get_register_user_use_case,
    get_request_password_reset_use_case,
)
from backend.modules.identity.api.schemas import (
    ConfirmEmailVerificationRequest,
    ConfirmPasswordResetRequest,
    EmailVerificationConfirmedResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    PasswordResetConfirmedResponse,
    PasswordResetRequestedResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    RequestPasswordResetRequest,
)
from backend.modules.identity.application import (
    ConfirmEmailVerificationCommand,
    ConfirmEmailVerificationUseCase,
    ConfirmPasswordResetCommand,
    ConfirmPasswordResetUseCase,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    LoginUserCommand,
    LoginUserUseCase,
    LogoutCommand,
    LogoutUseCase,
    RefreshAccessTokenUseCase,
    RefreshTokenCommand,
    RegisterUserCommand,
    RegisterUserUseCase,
    RequestPasswordResetCommand,
    RequestPasswordResetUseCase,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from backend.modules.identity.domain import (
    InactiveUserAuthenticationError,
    InvalidEmailVerificationTokenError,
    InvalidPasswordError,
    InvalidPasswordResetTokenError,
    User,
)

router = APIRouter(prefix="/auth", tags=["identity-auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(get_register_user_use_case),
) -> RegisterResponse:
    try:
        result = await use_case.execute(
            RegisterUserCommand(
                email=request.email,
                password=request.password,
            )
        )
        return RegisterResponse(user_id=result.user_id, email=result.email)
    except UserAlreadyExistsError as exc:
        raise AppException(
            code=ErrorCode.USER_ALREADY_EXISTS,
            message=str(exc),
            status_code=status.HTTP_409_CONFLICT,
        ) from exc
    except InvalidPasswordError as exc:
        raise AppException(
            code=ErrorCode.INVALID_PASSWORD,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    use_case: LoginUserUseCase = Depends(get_login_user_use_case),
) -> LoginResponse:
    try:
        result = await use_case.execute(
            LoginUserCommand(
                email=request.email,
                password=request.password,
            )
        )
        return LoginResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type=result.token_type,
        )
    except (InvalidCredentialsError, UserNotFoundError) as exc:
        raise AppException(
            code=ErrorCode.INVALID_CREDENTIALS,
            message="Invalid credentials",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc
    except InactiveUserAuthenticationError as exc:
        raise AppException(
            code=ErrorCode.INACTIVE_USER,
            message=str(exc),
            status_code=status.HTTP_403_FORBIDDEN,
        ) from exc


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh(
    request: RefreshTokenRequest,
    use_case: RefreshAccessTokenUseCase = Depends(get_refresh_access_token_use_case),
) -> RefreshTokenResponse:
    try:
        result = await use_case.execute(
            RefreshTokenCommand(refresh_token=request.refresh_token)
        )
        return RefreshTokenResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type=result.token_type,
        )
    except (InvalidRefreshTokenError, UserNotFoundError) as exc:
        raise AppException(
            code=ErrorCode.INVALID_REFRESH_TOKEN,
            message="Invalid refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc
    except InactiveUserAuthenticationError as exc:
        raise AppException(
            code=ErrorCode.INACTIVE_USER,
            message=str(exc),
            status_code=status.HTTP_403_FORBIDDEN,
        ) from exc


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout(
    request: LogoutRequest,
    use_case: LogoutUseCase = Depends(get_logout_use_case),
) -> LogoutResponse:
    # Idempotent — revokes the refresh token if it's active; an unknown, garbage, or
    # already-revoked/expired token is a silent no-op, so calling this twice (or with
    # a token that's expired anyway) is never an error.
    await use_case.execute(LogoutCommand(refresh_token=request.refresh_token))
    return LogoutResponse()


@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
async def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        user_id=str(current_user.id),
        email=current_user.email.value,
        status=current_user.status.value,
        email_verified=current_user.email_verified,
    )


@router.post(
    "/password-reset/request",
    response_model=PasswordResetRequestedResponse,
    status_code=status.HTTP_200_OK,
)
async def request_password_reset(
    request: RequestPasswordResetRequest,
    use_case: RequestPasswordResetUseCase = Depends(get_request_password_reset_use_case),
) -> PasswordResetRequestedResponse:
    # Always 200 with a generic body — never reveals whether the email exists.
    await use_case.execute(RequestPasswordResetCommand(email=request.email))
    return PasswordResetRequestedResponse()


@router.post(
    "/password-reset/confirm",
    response_model=PasswordResetConfirmedResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_password_reset(
    request: ConfirmPasswordResetRequest,
    use_case: ConfirmPasswordResetUseCase = Depends(get_confirm_password_reset_use_case),
) -> PasswordResetConfirmedResponse:
    try:
        await use_case.execute(
            ConfirmPasswordResetCommand(token=request.token, new_password=request.new_password)
        )
        return PasswordResetConfirmedResponse()
    except (InvalidPasswordResetTokenError, UserNotFoundError) as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except InvalidPasswordError as exc:
        raise AppException(
            code=ErrorCode.INVALID_PASSWORD,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc


@router.post(
    "/verify-email/confirm",
    response_model=EmailVerificationConfirmedResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_email_verification(
    request: ConfirmEmailVerificationRequest,
    use_case: ConfirmEmailVerificationUseCase = Depends(get_confirm_email_verification_use_case),
) -> EmailVerificationConfirmedResponse:
    try:
        await use_case.execute(ConfirmEmailVerificationCommand(token=request.token))
        return EmailVerificationConfirmedResponse()
    except (InvalidEmailVerificationTokenError, UserNotFoundError) as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc