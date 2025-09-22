import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath('.'))

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.services.auth import AuthService

from main import app
from src.database.models import Base, UserModel, Role
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

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_models():
    """Clean database and create tables before each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create test user for each test
    async with TestingSessionLocal() as session:
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

@pytest_asyncio.fixture(scope="function")
async def async_session():
    """Create a clean database session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()

@pytest.fixture(scope="function")
def client():
    """Test client that creates a new session for each test."""
    async def override_get_async_session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_async_session] = override_get_async_session
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
async def get_token(client):
    """Fixture to get an access token for authenticated tests."""
    form_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    response = client.post("/api/auth/login", data=form_data)
    assert response.status_code == 200, response.text
    return response.json()["access_token"]