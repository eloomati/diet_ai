from fastapi import APIRouter, Depends, status

from backend.shared.exceptions import AppException, ErrorCode

from backend.modules.identity.api.dependencies import (
    get_current_user,
    get_login_user_use_case,
    get_refresh_access_token_use_case,
    get_register_user_use_case,
)
from backend.modules.identity.api.schemas import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
)
from backend.modules.identity.application import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    LoginUserCommand,
    LoginUserUseCase,
    RefreshAccessTokenUseCase,
    RefreshTokenCommand,
    RegisterUserCommand,
    RegisterUserUseCase,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from backend.modules.identity.domain import (
    InactiveUserAuthenticationError,
    InvalidPasswordError,
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


@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
async def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        user_id=str(current_user.id),
        email=current_user.email.value,
        status=current_user.status.value,
    )