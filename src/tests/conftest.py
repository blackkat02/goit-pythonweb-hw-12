import sys
import os

sys.path.insert(0, os.path.abspath('.'))


import asyncio

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from src.database.models import Base, UserModel, ContactsModel 
from src.database.db import get_async_session
from src.services.auth import create_access_token, Hash

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user = {
    "username": "deadpool",
    "email": "deadpool@example.com",
    "password": "12345678",
    "role": "user",
}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    """
    Initializes the database models and creates a test user.
    This fixture runs once per module and handles the setup.
    """
    async def init_models():
        async with engine.begin() as conn:
            # Drop all tables and recreate them for a clean test environment
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            # Hash the password and create the test user
            hash_password = Hash().get_password_hash(test_user["password"])
            current_user = UserModel(
                username=test_user["username"],
                email=test_user["email"],
                hashed_password=hash_password,
                confirmed=True,
                avatar="https://twitter.com/gravatar",
                role=UserRole.USER,
            )
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    """
    Fixture to provide a TestClient with the database dependency overridden.
    This client will use the in-memory test database.
    """
    # Override the get_db dependency to use the test session
    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_async_session] = override_get_db

    yield TestClient(app)


@pytest_asyncio.fixture()
async def get_token(client):
    """
    Fixture to get an access token by making a real login request.
    This correctly simulates the user authentication flow.
    """
    form_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    response = client.post("/api/auth/login", data=form_data)
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
