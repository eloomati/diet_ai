import os

import pytest
from fastapi.testclient import TestClient

# Must be set before importing app/settings.
os.environ["TESTING"] = "true"

from backend.app.main import app
from backend.shared.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
