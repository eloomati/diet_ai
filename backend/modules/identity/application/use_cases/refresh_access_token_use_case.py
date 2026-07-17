from datetime import UTC, datetime, timedelta

from backend.modules.identity.application.dto.refresh_token_dto import (
    RefreshTokenCommand,
    RefreshTokenResult,
)
from backend.modules.identity.application.ports.refresh_token_repository import (
    RefreshTokenRepository,
)
from backend.modules.identity.application.ports.token_service import TokenService
from backend.modules.identity.application.use_cases.exceptions import (
    InvalidRefreshTokenError,
    UserNotFoundError,
)
from backend.modules.identity.domain import RefreshToken, UserRepository


class RefreshAccessTokenUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
        refresh_ttl_days: int = 7,
    ) -> None:
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._token_service = token_service
        self._refresh_ttl_days = refresh_ttl_days

    async def execute(self, command: RefreshTokenCommand) -> RefreshTokenResult:
        try:
            payload = self._token_service.decode_refresh_token(command.refresh_token)
            user_id = payload["sub"]
        except Exception as exc:
            raise InvalidRefreshTokenError("Invalid refresh token.") from exc

        # W tym etapie trzymamy prosty hash = raw token (można potem utwardzić)
        stored = await self._refresh_token_repository.get_active_by_token_hash(command.refresh_token)
        if not stored:
            raise InvalidRefreshTokenError("Refresh token not active.")

        user = await self._user_repository.get_by_id(stored.user_id)
        if not user:
            raise UserNotFoundError("User not found.")

        user.assert_can_authenticate()

        await self._refresh_token_repository.revoke(stored.id)

        new_refresh_raw = self._token_service.create_refresh_token(str(user.id))
        new_refresh = RefreshToken.issue(
            user_id=user.id,
            token_hash=new_refresh_raw,
            expires_at=datetime.now(UTC) + timedelta(days=self._refresh_ttl_days),
        )
        await self._refresh_token_repository.save(new_refresh)

        new_access = self._token_service.create_access_token(str(user.id), user.email.value)

        return RefreshTokenResult(
            access_token=new_access,
            refresh_token=new_refresh_raw,
        )