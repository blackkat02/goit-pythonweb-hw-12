import sys
import os

sys.path.insert(0, os.path.abspath('.'))


import asyncio

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.services.auth import AuthService

from main import app
from src.database.models import Base, UserModel, Role, ContactsModel 
from src.database.db import get_async_session


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
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            # Оновіть цей рядок:
            # hash_password = Hash().get_password_hash(test_user["password"])

            auth_service = AuthService()
            hash_password = auth_service.hash_password(test_user["password"])

            current_user = UserModel(
                username=test_user["username"],
                email=test_user["email"],
                hashed_password=hash_password,
                confirmed=True,
                avatar="https://twitter.com/gravatar",
                role=Role.USER,
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


from collections.abc import AsyncGenerator


@pytest_asyncio.fixture()
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an isolated async database session for unit tests.
    Each test runs in a transaction that is rolled back at the end.
    """
    async with TestingSessionLocal() as session:
        # Begin a transaction
        async with session.begin():
            yield session

