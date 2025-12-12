from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Базовая схема пользователя.

    Содержит общие поля, используемые для отображения
    и частичного обновления данных пользователя.
    """
    username: Optional[str] = Field(None, description="Имя пользователя")
    email: Optional[EmailStr] = Field(None, description="Email пользователя")
    phone: Optional[str] = Field(None, description="Номер телефона")


class UserCreate(UserBase):
    """
    Схема для создания нового пользователя.

    Используется при регистрации. Содержит обязательный пароль,
    который в дальнейшем будет захеширован.
    """
    username: str = Field(..., description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., min_length=6, description="Пароль")


class UserUpdate(UserBase):
    """
    Схема для обновления данных пользователя.

    Позволяет менять только переданные поля.
    Пароль, если указан, будет обновлён и сохранён в виде хеша.
    """
    password: Optional[str] = Field(None, min_length=6, description="Новый пароль")


class UserOut(UserBase):
    """
    Схема для отображения данных пользователя.

    Используется для отдачи данных клиенту (например, в API).
    Не содержит пароль и другие чувствительные данные.
    """
    id: int = Field(..., description="ID пользователя")

    class Config:
        from_attributes = True
