from app.schemas import APIRequestCreate
import pytest

from fastapi.testclient import TestClient
from app.main import app
from pytest import fixture

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models
from app.database import get_db
from app.models import User
from app.auth import hash_password

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

test_engine = create_engine(TEST_DATABASE_URL)  # Engine -> knows WHERE the database is  # Session -> actually interacts with the database

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

Base.metadata.create_all(bind=test_engine)

# client = TestClient(app)
# @fixture
# def client():
#     return TestClient(app)

# A fixture is basically test setup that pytest can provide to a test automatically. fixture -> prepare something -> test uses it
@pytest.fixture
def db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user(db):
    user = User(
        username="pytest_user",
        email="pytest@example.com",
        hashed_password=hash_password("test_password")
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    yield user

    db.delete(user)
    db.commit()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()



def test_valid_api_request():
    request = APIRequestCreate(
        endpoint="/test",
        response_time=120.5,
        method="GET",
        status_code=200,
        ip_address="127.0.0.1"
    )

    assert request.endpoint == "/test"
    assert request.response_time == 120.5
    assert request.method == "GET"
    assert request.status_code == 200
    assert request.ip_address == "127.0.0.1"

def test_negative_response_time():
    with pytest.raises(ValueError):
        APIRequestCreate(
            endpoint="/test",
            response_time=-50,
            method="GET",
            status_code=200,
            ip_address="127.0.0.1"
        )

def test_invalid_status_code():
    with pytest.raises(ValueError):
        APIRequestCreate(
            endpoint="/test",
            response_time=120.5,
            method="GET",
            status_code=700,
            ip_address="127.0.0.1"
        )

def test_empty_endpoint():
    with pytest.raises(ValueError):
        APIRequestCreate(
            endpoint="",
            response_time=120.5,
            method="GET",
            status_code=200,
            ip_address="127.0.0.1"
        )

def test_invalid_method():
    with pytest.raises(ValueError):
        APIRequestCreate(
            endpoint="/test",
            response_time=120.5,
            method="BANANA",
            status_code=200,
            ip_address="127.0.0.1"
        )

def test_api_is_running(client):
    response = client.get("/docs")

    assert response.status_code == 200

def test_login(client, test_user):
    response = client.post(
        "/login",
        data={
            "username": "pytest_user",
            "password": "test_password"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_create_api_request(client, test_user):
    login_response = client.post(
        "/login",
        data={
            "username": "pytest_user",
            "password": "test_password"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/requests",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "endpoint": "/test",
            "response_time": 120.5,
            "method": "GET",
            "status_code": 200,
            "ip_address": "127.0.0.1"
        }
    )

    assert response.status_code == 200
    assert response.json()["message"] == "API request saved successfully"
    assert "id" in response.json()

def test_login_wrong_password(client, test_user):
    response = client.post(
        "/login",
        data={
            "username": "pytest_user",
            "password": "wrong_password"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_create_api_request_without_token(client):
    response = client.post(
        "/api/requests",
        json={
            "endpoint": "/test",
            "response_time": 120.5,
            "method": "GET",
            "status_code": 200,
            "ip_address": "127.0.0.1"
        }
    )

    assert response.status_code == 401

def test_create_api_request_invalid_data(client, test_user):
    login_response = client.post(
        "/login",
        data={
            "username": "pytest_user",
            "password": "test_password"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/requests",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "endpoint": "/test",
            "response_time": 120.5,
            "method": "GET",
            "status_code": "invalid",
            "ip_address": "127.0.0.1"
        }
    )

    assert response.status_code == 422

def test_login_nonexistent_user(client):
    response = client.post(
        "/login",
        data={
            "username": "user_does_not_exist",
            "password": "test_password"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"