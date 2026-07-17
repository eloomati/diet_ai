from backend.modules.identity.application.dto.logout_dto import LogoutCommand
from backend.modules.identity.application.ports.refresh_token_repository import (
    RefreshTokenRepository,
)


class LogoutUseCase:
    """Revokes the given refresh token. Idempotent — an unknown, garbage, or
    already-revoked/expired token is a silent no-op, since the end state the caller
    wants ("this token can no longer be used") already holds either way."""

    def __init__(self, refresh_token_repository: RefreshTokenRepository) -> None:
        self._refresh_token_repository = refresh_token_repository

    async def execute(self, command: LogoutCommand) -> None:
        stored = await self._refresh_token_repository.get_active_by_token_hash(
            command.refresh_token
        )
        if stored is not None:
            await self._refresh_token_repository.revoke(stored.id)
