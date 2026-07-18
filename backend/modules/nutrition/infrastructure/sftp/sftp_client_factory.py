from backend.modules.nutrition.application.ports.sftp_client import SftpClient
from backend.modules.nutrition.infrastructure.sftp.asyncssh_sftp_client import AsyncSshSftpClient
from backend.modules.nutrition.infrastructure.sftp.mock_sftp_client import MockSftpClient
from backend.shared.config.settings import Settings


def build_sftp_client(settings: Settings) -> SftpClient:
    if settings.sftp_provider == "mock":
        return MockSftpClient()

    if settings.sftp_provider == "sftp":
        return AsyncSshSftpClient(
            host=settings.sftp_host,
            port=settings.sftp_port,
            username=settings.sftp_username,
            password=settings.sftp_password,
            remote_dir=settings.sftp_remote_dir,
        )

    raise ValueError(f"Unknown SFTP_PROVIDER: {settings.sftp_provider!r} (expected mock|sftp).")
