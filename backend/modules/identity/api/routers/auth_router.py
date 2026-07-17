from fastapi import APIRouter, Depends, HTTPException, status

from backend.modules.identity.api.dependencies import (
    get_login_user_use_case,
    get_refresh_access_token_use_case,
    get_register_user_use_case,
)
from backend.modules.identity.api.schemas import (
    LoginRequest,
    LoginResponse,
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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidPasswordError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc
    except InactiveUserAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
    except InactiveUserAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc