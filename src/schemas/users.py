from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime

from src.database.models import Role

# --- Базові схеми ---


class UserBaseSchema(BaseModel):
    """
    Базова схема для користувача, що містить загальні поля.
    Використовується для створення інших, специфічних схем.
    """

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


# --- Схеми для реєстрації та входу ---


class UserCreateSchema(UserBaseSchema):
    """
    Схема для реєстрації нового користувача.
    Включає поле password та avatar, які необхідні під час реєстрації.
    """

    password: str = Field(min_length=6)
    avatar: str | None = None 
    confirmed: bool = False 


class UserLoginSchema(BaseModel):
    """
    Схема для входу в систему.
    """

    email: EmailStr
    password: str = Field(min_length=6)


# --- Схеми для відповіді API ---


class UserResponseSchema(UserBaseSchema):
    """
    Схема для повернення даних користувача.
    Не містить пароля, але включає ID та інші службові поля.
    """

    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str | None
    confirmed: bool
    role: Role

    model_config = ConfigDict(from_attributes=True)


# --- Схема для оновлення даних користувача ---


class UserUpdateSchema(BaseModel):
    """
    Схема для часткового оновлення даних користувача.
    Всі поля є опціональними. Пароль оновлюється окремим запитом.
    """

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    # Виправлено: avatar тепер має коректну довжину.
    avatar: Optional[str] = Field(None, min_length=3, max_length=255)


class TokenSchema(BaseModel):
    """
    Схема для JWT-токенів.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

  
class UserUpdatePasswordSchema(BaseModel):
    """
    Схема для оновлення пароля користувача.
    """
    new_password: str = Field(min_length=6, max_length=50)
