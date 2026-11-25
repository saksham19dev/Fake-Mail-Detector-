import os
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import init_db
import asyncio


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database schema is initialized before test execution."""
    asyncio.run(init_db())
    yield


@pytest.fixture
def client():
    """Synchronous test client for FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client
