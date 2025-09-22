import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException, status
from src.database.models import UserModel, Role
from src.services.permissions import RoleChecker


@pytest.mark.asyncio
async def test_role_checker_allowed():
    """Test RoleChecker when the user has the required role."""
    # Створюємо заглушку для користувача з роллю 'admin'
    mock_user = MagicMock(spec=UserModel)
    mock_user.role = Role.ADMIN
    
    # Визначаємо ролі, які дозволені для цього тесту
    required_roles = [Role.ADMIN, Role.MODERATOR]
    
    # Створюємо екземпляр RoleChecker
    role_checker = RoleChecker(required_roles)
    
    # Викликаємо __call__ з нашою заглушкою користувача
    try:
        await role_checker(user=mock_user)
    except HTTPException:
        pytest.fail("HTTPException was raised for an allowed role.")


@pytest.mark.asyncio
async def test_role_checker_forbidden():
    """Test RoleChecker when the user does not have the required role."""
    # Створюємо заглушку для користувача з роллю 'user'
    mock_user = MagicMock(spec=UserModel)
    mock_user.role = Role.USER
    
    # Визначаємо ролі, які заборонені
    required_roles = [Role.ADMIN, Role.MODERATOR]
    
    # Створюємо екземпляр RoleChecker
    role_checker = RoleChecker(required_roles)

    # Перевіряємо, чи викидається HTTPException
    with pytest.raises(HTTPException) as excinfo:
        await role_checker(user=mock_user)

    # Перевіряємо, що код стану і текст помилки відповідають очікуванням
    assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
    assert excinfo.value.detail == "Operation forbidden: insufficient permissions."

