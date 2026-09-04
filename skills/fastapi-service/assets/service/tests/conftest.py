import os

import pytest

os.environ.setdefault("APP_LLM_BASE_URL", "http://gw.test")
os.environ.setdefault("APP_LLM_API_KEY", "test-key")
os.environ.setdefault("APP_ENV", "test")

from fastapi.testclient import TestClient  # noqa: E402

from {{pkg}}.core.config import get_settings  # noqa: E402
from {{pkg}}.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c
