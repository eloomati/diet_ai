import pytest

from backend.shared.config.settings import Settings

SHORT_KEY = "too-short"
LONG_KEY = "a" * 32


def test_rejects_a_short_jwt_secret_outside_dev_and_testing() -> None:
    with pytest.raises(ValueError, match="jwt_secret_key must be at least 32 bytes"):
        Settings(app_env="production", testing=False, jwt_secret_key=SHORT_KEY)


def test_accepts_a_short_jwt_secret_in_dev() -> None:
    settings = Settings(app_env="dev", testing=False, jwt_secret_key=SHORT_KEY)

    assert settings.jwt_secret_key == SHORT_KEY


def test_accepts_a_short_jwt_secret_when_testing() -> None:
    settings = Settings(app_env="production", testing=True, jwt_secret_key=SHORT_KEY)

    assert settings.jwt_secret_key == SHORT_KEY


def test_accepts_a_long_enough_jwt_secret_outside_dev() -> None:
    settings = Settings(app_env="production", testing=False, jwt_secret_key=LONG_KEY)

    assert settings.jwt_secret_key == LONG_KEY
