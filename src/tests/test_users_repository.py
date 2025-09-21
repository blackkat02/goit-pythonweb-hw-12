import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from src.database.models import UserModel
from src.schemas.users import UserCreateSchema
from src.repository.users import UserRepository


@pytest.mark.asyncio
async def test_create_user():
    # 1. Підготовка (Arrange)
    db_mock = AsyncMock()
    user_repo = UserRepository(db=db_mock)
    
    user_in_data = UserCreateSchema(
        username="testuser",
        email="testuser@example.com",
        avatar=None,
        confirmed=False
    )
    hashed_password = "hashed_password123"
    
    # Створення об'єкта UserModel, який ми очікуємо отримати
    expected_user = UserModel(
        username=user_in_data.username,
        email=user_in_data.email,
        hashed_password=hashed_password,
        avatar=None,
        confirmed=False
    )

    # Імітуємо поведінку db.refresh, щоб вона повертала об'єкт користувача
    db_mock.refresh.return_value = expected_user
    
    # 2. Дія (Act)
    created_user = await user_repo.create_user(user_in=user_in_data, hashed_password=hashed_password)
    
    # 3. Перевірка (Assert)
    # Перевіряємо, що методи були викликані з правильними аргументами
    db_mock.add.assert_called_once()
    added_user = db_mock.add.call_args.args[0]
    assert added_user.username == user_in_data.username
    assert added_user.email == user_in_data.email
    assert added_user.hashed_password == hashed_password
    assert added_user.confirmed == False

    db_mock.commit.assert_called_once()
    db_mock.refresh.assert_called_once_with(added_user)
    
    # Перевіряємо, що повернутий об'єкт відповідає очікуваному
    assert created_user == added_user

