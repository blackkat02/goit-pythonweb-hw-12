import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.users import UserCreateSchema
from src.repository.users import UserRepository
from src.database.models import UserModel
from src.services.auth import AuthService
from src.tests.conftest import TestingSessionLocal, test_user 

@pytest.fixture
async def db_session():
    """
    Provides an async database session for testing.
    """
    async with TestingSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_create_user(async_session: AsyncSession):
    repo = UserRepository(async_session)

    user_data = UserCreateSchema(
        username="test_user",
        email="test_user@example.com",
        password="testpassword",
        avatar="https://test.com/avatar"
    )

    auth_service = AuthService()
    hashed_password = auth_service.hash_password(user_data.password)

    new_user = await repo.create_user(user_data, hashed_password)

    assert new_user.username == "test_user"
    assert new_user.email == "test_user@example.com"


    # Assert: Verify the results
    assert new_user is not None
    assert new_user.username == "test_user"
    assert new_user.email == "test_user@example.com"
    assert new_user.hashed_password == hashed_password
    assert isinstance(new_user, UserModel)
    
    # Optional: Verify the user was saved to the database
    retrieved_user = await repo.get_user_by_email("test_user@example.com")
    assert retrieved_user is not None
    assert retrieved_user.username == "test_user"


@pytest.mark.asyncio
async def test_get_user_by_email(async_session: AsyncSession):
    """
    Test the get_user_by_email method of the UserRepository.
    It verifies if a user can be retrieved from the database by their email.
    """
    repo = UserRepository(async_session)
    
    # Arrange: Create a user to be retrieved
    user_data = UserCreateSchema(
        username="email_test_user",
        email="email_test@example.com",
        password="testpassword",
        avatar="https://test.com/avatar"
    )

    auth_service = AuthService()
    hashed_password = auth_service.hash_password(user_data.password)

    # Note: We need to create the user in the database first for the test to work
    new_user = await repo.create_user(user_data, hashed_password)
    
    # Act: Call the method we are testing
    retrieved_user = await repo.get_user_by_email("email_test@example.com")
    
    # Assert: Verify the results
    assert retrieved_user is not None
    assert retrieved_user.username == "email_test_user"
    assert retrieved_user.email == "email_test@example.com"
    assert retrieved_user.id == new_user.id


@pytest.mark.asyncio
async def test_get_user_by_id(async_session: AsyncSession):
    """
    Test the get_user_by_id method of the UserRepository.
    It verifies if a user can be retrieved from the database by their ID.
    """
    repo = UserRepository(async_session)

    # Arrange: Create a user and save it to the database
    user_data = UserCreateSchema(
        username="id_test_user",
        email="id_test@example.com",
        password="testpassword",
        avatar="https://test.com/avatar"
    )
    auth_service = AuthService()
    hashed_password = auth_service.hash_password(user_data.password)

    new_user = await repo.create_user(user_data, hashed_password)
    
    # Act: Call the method we are testing with the user's ID
    retrieved_user = await repo.get_user_by_id(new_user.id)
    
    # Assert: Verify the results
    assert retrieved_user is not None
    assert retrieved_user.id == new_user.id
    assert retrieved_user.username == "id_test_user"
    assert retrieved_user.email == "id_test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(async_session: AsyncSession):
    """
    Test the get_user_by_id method when the user does not exist.
    It should return None.
    """
    repo = UserRepository(async_session)

    # Act: Try to get a user with an ID that definitely does not exist
    non_existent_id = 999999
    retrieved_user = await repo.get_user_by_id(non_existent_id)
    
    # Assert: Verify that the result is None
    assert retrieved_user is None


@pytest.mark.asyncio
async def test_update_user_avatar(async_session: AsyncSession):
    """
    Test the update_user_avatar method.
    It verifies if a user's avatar can be successfully updated.
    """
    repo = UserRepository(async_session)

    # Arrange: Create a user with an initial avatar
    user_data = UserCreateSchema(
        username="avatar_test_user",
        email="avatar_test@example.com",
        password="testpassword",
        avatar="https://old.avatar.com"
    )
    auth_service = AuthService()
    hashed_password = auth_service.hash_password(user_data.password)
    new_user = await repo.create_user(user_data, hashed_password)
    
    # Act: Update the user's avatar
    new_avatar_url = "https://new.avatar.com"
    updated_user = await repo.update_user_avatar(new_user.id, new_avatar_url)
    
    # Assert: Verify that the avatar has been updated in the returned object
    assert updated_user is not None
    assert updated_user.avatar == new_avatar_url
    assert updated_user.id == new_user.id
    
    # Optional: Verify the change persisted in the database
    retrieved_user = await repo.get_user_by_id(new_user.id)
    assert retrieved_user.avatar == new_avatar_url


@pytest.mark.asyncio
async def test_change_confirmed_email(async_session: AsyncSession):
    """
    Test the change_confirmed_email method.
    It verifies if a user's 'confirmed' status can be updated.
    """
    repo = UserRepository(async_session)

    # Arrange: Create a user with confirmed=False
    user_data = UserCreateSchema(
        username="confirm_test_user",
        email="confirm_test@example.com",
        password="testpassword",
        confirmed=False
    )
    auth_service = AuthService()
    hashed_password = auth_service.hash_password(user_data.password)
    new_user = await repo.create_user(user_data, hashed_password)
    
    # Assert initial state
    assert new_user.confirmed is False

    # Act: Call the method to change the status
    await repo.change_confirmed_email(new_user.email)
    
    # Assert: Verify the status has been updated in the database
    retrieved_user = await repo.get_user_by_email(new_user.email)
    assert retrieved_user.confirmed is True


@pytest.mark.asyncio
async def test_get_user_by_username(async_session: AsyncSession):
    """
    Test the get_user_by_username method.
    It verifies if a user can be retrieved from the database by their username.
    """
    repo = UserRepository(async_session)
    
    # Arrange: Створюємо користувача для тестування
    user_data = UserCreateSchema(
        username="username_test_user",
        email="username_test@example.com",
        password="testpassword",
        avatar="https://test.com/avatar"
    )
    auth_service = AuthService()
    hashed_password = auth_service.hash_password(user_data.password)
    new_user = await repo.create_user(user_data, hashed_password)
    
    # Act: Викликаємо метод для отримання користувача
    retrieved_user = await repo.get_user_by_username("username_test_user")
    
    # Assert: Перевіряємо, що користувач був знайдений і дані збігаються
    assert retrieved_user is not None
    assert retrieved_user.username == "username_test_user"
    assert retrieved_user.email == "username_test@example.com"
    assert retrieved_user.id == new_user.id


@pytest.mark.asyncio
async def test_update_password(async_session: AsyncSession):
    """
    Test the update_password method.
    It verifies that a user's password can be successfully updated.
    """
    repo = UserRepository(async_session)

    # Arrange: Створюємо користувача
    user_data = UserCreateSchema(
        username="password_update_user",
        email="password_update@example.com",
        password="old_password",
        avatar="https://test.com/avatar"
    )
    auth_service = AuthService()
    hashed_password_old = auth_service.hash_password(user_data.password)
    user_to_update = await repo.create_user(user_data, hashed_password_old)
    
    # Act: Оновлюємо пароль
    new_password = "new_password"
    hashed_password_new = auth_service.hash_password(new_password)
    updated_user = await repo.update_password(user_to_update, hashed_password_new)

    # Assert: Перевіряємо, що пароль оновлено і хеші не збігаються
    assert updated_user is not None
    assert updated_user.hashed_password != hashed_password_old
    assert updated_user.hashed_password == hashed_password_new


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(async_session: AsyncSession):
    """
    Test the get_user_by_username method when the user does not exist.
    It should return None.
    """
    repo = UserRepository(async_session)
    
    # Act: Намагаємося отримати неіснуючого користувача
    retrieved_user = await repo.get_user_by_username("non_existent_username")
    
    # Assert: Перевіряємо, що результат - None
    assert retrieved_user is None


@pytest.mark.asyncio
async def test_get_users_with_pagination(async_session: AsyncSession):
    """Test retrieving users with pagination."""
    repo = UserRepository(async_session)
    auth_service = AuthService()

    # Create unique users for pagination test
    for i in range(10):
        user_data = UserCreateSchema(
            username=f"pag_user_{i}",
            email=f"pag_user_{i}@example.com",
            password="testpassword"
        )
        hashed_password = auth_service.hash_password(user_data.password)
        await repo.create_user(user_data, hashed_password)

    skip, limit = 2, 3
    retrieved_users = await repo.get_users(skip=skip, limit=limit)

    assert len(retrieved_users) == limit
    # Users should be ordered by ID, so we check the first user's username
    assert retrieved_users[0].username.startswith("pag_user_")
