import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.database import get_db
from backend.app.main import app

# In-memory SQLite for isolated, fast, reliable tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a clean SQLAlchemy session for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a TestClient with overridden get_db and mocked email delivery."""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("backend.app.api.v1.auth.register.send_otp_email"),
        patch("backend.app.api.v1.auth.resend_otp.send_otp_email"),
        patch(
            "backend.app.api.v1.auth.forgot_password.send_password_reset_email"
        ),
        patch("backend.app.core.config.settings.ai_assistant_provider", "mock"),
    ):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()
