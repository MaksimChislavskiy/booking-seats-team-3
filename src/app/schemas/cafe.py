from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.app.core.constants import (
    CAFE_ADDRESS_MAX_LENGTH,
    CAFE_NAME_MAX_LENGTH,
    CAFE_PHONE_MAX_LENGTH,
)


class CafeBase(BaseModel):
    """Общие поля для всех схем Cafe."""

    name: str = Field(
        ...,
        max_length=CAFE_NAME_MAX_LENGTH,
        description='Название кафе',
    )
    address: str = Field(
        ...,
        max_length=CAFE_ADDRESS_MAX_LENGTH,
        description='Адрес кафе',
    )
    phone: str = Field(
        ...,
        max_length=CAFE_PHONE_MAX_LENGTH,
        description='Телефон кафе',
    )
    description: str | None = None
    photo_id: UUID | None = None
    managers: list[int] = Field(
        default_factory=list,
        description='ID менеджеров кафе',
    )


class CafeCreate(CafeBase):
    """Схема для создания нового кафе."""

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        """Название не может быть пустым."""
        if not value.strip():
            raise ValueError('Название кафе не может быть пустым')
        return value.strip()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """Проверка формата телефона."""
        value_clean = (
            value.replace(' ', '')
            .replace('-', '')
            .replace('(', '')
            .replace(')', '')
        )
        if not value_clean.isdigit():
            raise ValueError('Телефон должен содержать только цифры')
        if len(value_clean) not in (10, 11):
            raise ValueError('Телефон должен содержать 10 или 11 цифр')
        if value_clean.startswith('8'):
            value_clean = '7' + value_clean[1:]
        elif not value_clean.startswith('7'):
            raise ValueError('Телефон должен начинаться с 7 или 8')
        return value_clean

    @field_validator('photo_id')
    @classmethod
    def validate_photo_id(cls, value: UUID | None) -> UUID | None:
        """photo_id должен быть корректным UUID."""
        if value is None:
            return value
        try:
            UUID(str(value))
        except ValueError:
            raise ValueError('photo_id должен быть корректным UUID')
        return value


class CafeUpdate(BaseModel):
    """Схема для частичного обновления кафе."""

    name: str | None = Field(None, max_length=CAFE_NAME_MAX_LENGTH)
    address: str | None = Field(None, max_length=CAFE_ADDRESS_MAX_LENGTH)
    phone: str | None = Field(None, max_length=CAFE_PHONE_MAX_LENGTH)
    description: str | None = None
    photo_id: UUID | None = None
    managers: list[int] | None = None

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, value: str | None) -> str | None:
        """Название не может быть пустым (если передано)."""
        if value is not None and not value.strip():
            raise ValueError('Название кафе не может быть пустым')
        return value.strip() if value is not None else value

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Проверка формата телефона (если передано)."""
        if value is None:
            return value
        value_clean = (
            value.replace(' ', '')
            .replace('-', '')
            .replace('(', '')
            .replace(')', '')
        )
        if not value_clean.isdigit():
            raise ValueError('Телефон должен содержать только цифры')
        if len(value_clean) not in (10, 11):
            raise ValueError('Телефон должен содержать 10 или 11 цифр')
        if value_clean.startswith('8'):
            value_clean = '7' + value_clean[1:]
        elif not value_clean.startswith('7'):
            raise ValueError('Телефон должен начинаться с 7 или 8')
        return value_clean

    @field_validator('photo_id')
    @classmethod
    def validate_photo_id(cls, value: UUID | None) -> UUID | None:
        """photo_id должен быть корректным UUID (если передано)."""
        if value is None:
            return value
        try:
            UUID(str(value))
        except ValueError:
            raise ValueError('photo_id должен быть корректным UUID')
        return value


class CafeRead(CafeBase):
    """Схема для чтения/списка кафе."""

    id: int
    created_at: datetime
    updated_at: datetime
    active: bool

    class Config:
        """Конфигурация Pydantic для работы с ORM."""

        from_attributes = True


class CafeShortInfo(BaseModel):
    """Укороченная схема для чтения кафе (для списков)."""

    id: int
    name: str
    address: str
    phone: str
    photo_id: UUID | None

    class Config:
        """Конфигурация Pydantic для работы с ORM."""

        from_attributes = True
