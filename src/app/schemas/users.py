# TODO: Перепроверить схемы по Swagger
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    model_validator,
)

from app.core.constants import MIN_LENGTH_USER_PASSWORD


class UserBase(BaseModel):
    """Базовая схема пользователя.

    Содержит общие поля, используемые для отображения
    и частичного обновления данных пользователя.
    """

    username: Optional[str] = Field(
        None,
        description="Имя пользователя",
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Email пользователя",
    )
    phone: Optional[str] = Field(
        None,
        description="Номер телефона",
    )


class UserCreate(UserBase):
    """Схема для создания нового пользователя.

    Используется при регистрации.
    Обязательные поля:
    - username
    - password
    - email или phone
    """

    username: str = Field(
        ...,
        description="Имя пользователя",
    )
    password: str = Field(
        ...,
        min_length=MIN_LENGTH_USER_PASSWORD,
        description="Пароль",
    )

    @model_validator(mode="after")
    def validate_email_or_phone(self) -> "UserCreate":
        """Проверяет, что указан email или phone."""
        if not self.email and not self.phone:
            raise ValueError("Необходимо указать email или номер телефона")
        return self


class UserUpdate(UserBase):
    """Схема для обновления данных пользователя.

    Позволяет менять только переданные поля.
    Пароль, если указан, будет обновлён и сохранён в виде хеша.
    """

    password: Optional[str] = Field(
        None,
        min_length=MIN_LENGTH_USER_PASSWORD,
        description="Новый пароль",
    )


class UserOut(UserBase):
    """Схема для отображения данных пользователя.

    Используется для отдачи данных клиенту (например, в API).
    Не содержит пароль и другие чувствительные данные.
    """

    id: int = Field(
        ...,
        description="ID пользователя",
    )

    class Config:
        """Конфигурация Pydantic для работы с ORM."""

        from_attributes = True
