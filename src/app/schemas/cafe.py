import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

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

    model_config = ConfigDict(extra='forbid')

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        """Проверка названия кафе на пустоту."""
        if not value.strip():
            raise ValueError('Название кафе не может быть пустым')
        return value.strip()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """Проверка формата телефона с использованием регулярного выражения."""
        cleaned = re.sub(r'\D', '', value)
        if not re.match(r'^7\d{10}$', cleaned):
            raise ValueError(
                'Телефон должен быть в формате +7 или 8 с 10 цифрами после',
            )
        return cleaned


class CafeUpdate(BaseModel):
    """Схема для частичного обновления кафе."""

    model_config = ConfigDict(extra='forbid')

    name: str | None = Field(None, max_length=CAFE_NAME_MAX_LENGTH)
    address: str | None = Field(None, max_length=CAFE_ADDRESS_MAX_LENGTH)
    phone: str | None = Field(None, max_length=CAFE_PHONE_MAX_LENGTH)
    description: str | None = None
    photo_id: UUID | None = None
    managers: list[int] | None = None

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, value: str | None) -> str | None:
        """Проверка названия кафе на пустоту (если передано)."""
        if value is not None and not value.strip():
            raise ValueError('Название кафе не может быть пустым')
        return value.strip() if value is not None else value

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Проверка формата телефона (если передано)."""
        if value is None:
            return value
        cleaned = re.sub(r'\D', '', value)
        if not re.match(r'^7\d{10}$', cleaned):
            raise ValueError(
                'Телефон должен быть в формате +7 или 8 с 10 цифрами после',
            )
        return cleaned


class CafeInfo(CafeBase):
    """Схема для чтения информации о кафе."""

    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CafeShortInfo(BaseModel):
    """Укороченная схема для списков кафе."""

    id: int
    name: str
    address: str
    phone: str
    description: str | None
    photo_id: UUID | None

    model_config = ConfigDict(from_attributes=True)
