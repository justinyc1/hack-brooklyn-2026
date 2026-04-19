import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from main import app
from auth.clerk import require_auth
from db import db as real_db


FAKE_USER_ID = "user_test123"
FAKE_SESSION_ID = "507f1f77bcf86cd799439011"


def override_require_auth():
    return FAKE_USER_ID


@pytest.fixture
def client():
    app.dependency_overrides[require_auth] = override_require_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("db.db", mock)
    try:
        monkeypatch.setattr("routes.code.db", mock)
    except (ImportError, AttributeError):
        # routes.code doesn't exist yet; this is OK since mock_db is only used by future tests
        pass
    return mock
