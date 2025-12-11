from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.core.constants import (
    CAFE_ADDRESS_MAX_LENGTH,
    CAFE_NAME_MAX_LENGTH,
    CAFE_PHONE_MAX_LENGTH,
)


class CafeBase(BaseModel):
    """Общие поля для всех схем Cafe."""

    name: str = Field(
        ...,
        max_length=CAFE_NAME_MAX_LENGTH,
        description="Название кафе",
    )
    address: str = Field(
        ...,
        max_length=CAFE_ADDRESS_MAX_LENGTH,
        description="Адрес кафе",
    )
    phone: str = Field(
        ...,
        max_length=CAFE_PHONE_MAX_LENGTH,
        description="Телефон",
    )
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers: List[int] = Field(
        default_factory=list,
        description="ID менеджеров",
    )


class CafeCreate(CafeBase):
    """Схема для создания нового кафе."""

    @validator("phone")
    def validate_phone(self, v: str) -> str:
        """Проверка телефона: только цифры."""
        if not v.isdigit():
            raise ValueError("Телефон должен содержать только цифры")
        return v


class CafeUpdate(CafeBase):
    """Схема для частичного обновления кафе."""

    name: Optional[str] = Field(
        None,
        max_length=CAFE_NAME_MAX_LENGTH,
    )
    address: Optional[str] = Field(
        None,
        max_length=CAFE_ADDRESS_MAX_LENGTH,
    )
    phone: Optional[str] = Field(
        None,
        max_length=CAFE_PHONE_MAX_LENGTH,
    )
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers: Optional[List[int]] = None


class CafeRead(CafeBase):
    """Схема для чтения/списка кафе (с id и датами)."""

    id: int
    created_at: str
    updated_at: str
    active: bool

    class Config:
        """Конфигурация Pydantic."""

        from_attributes = True


class CafeInDB(CafeRead):
    """Схема для внутренних операций."""
