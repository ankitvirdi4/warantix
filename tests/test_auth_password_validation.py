import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import PASSWORD_MAX_LENGTH
from app.database import Base
from app.deps import get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _signup(client: TestClient, email: str, password: str):
    return client.post(
        "/api/v1/auth/signup",
        json={"email": email, "name": "Test User", "password": password},
    )


def _login(client: TestClient, email: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_signup_allows_password_at_max_length(client: TestClient):
    password = "A" * PASSWORD_MAX_LENGTH
    response = _signup(client, "max@example.com", password)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "max@example.com"


def test_signup_rejects_password_above_max_length(client: TestClient):
    password = "B" * (PASSWORD_MAX_LENGTH + 1)
    response = _signup(client, "toolong@example.com", password)
    assert response.status_code == 422


def test_login_with_max_length_password_succeeds(client: TestClient):
    password = "C" * PASSWORD_MAX_LENGTH
    email = "loginmax@example.com"
    signup_response = _signup(client, email, password)
    assert signup_response.status_code == 200

    login_response = _login(client, email, password)
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_login_rejects_password_above_max_length(client: TestClient):
    password = "D" * (PASSWORD_MAX_LENGTH + 1)
    response = _login(client, "nosuchuser@example.com", password)
    assert response.status_code == 422
