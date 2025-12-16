from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

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
        description="Телефон кафе",
    )
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers: List[int] = Field(
        default_factory=list,
        description="ID менеджеров кафе",
    )


class CafeCreate(CafeBase):
    """Схема для создания нового кафе."""

    @validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Проверка, что название не пустое."""
        if not v.strip():
            raise ValueError("Название кафе не может быть пустым")
        return v.strip()

    @validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Проверка формата телефона."""
        v_clean = (
            v.replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )
        if not v_clean.isdigit():
            raise ValueError("Телефон должен содержать только цифры")
        if len(v_clean) not in (10, 11):
            raise ValueError("Телефон должен содержать 10 или 11 цифр")
        if v_clean.startswith("8"):
            v_clean = "7" + v_clean[1:]
        elif not v_clean.startswith("7"):
            raise ValueError("Телефон должен начинаться с 7 или 8")
        return v_clean

    @validator("photo_id")
    @classmethod
    def validate_photo_id(cls, v: Optional[UUID]) -> Optional[UUID]:
        """Проверка корректности UUID для photo_id."""
        if v is None:
            return v
        try:
            UUID(str(v))
        except ValueError:
            raise ValueError("photo_id должен быть корректным UUID")
        return v


class CafeUpdate(CafeBase):
    """Схема для частичного обновления кафе."""

    name: Optional[str] = Field(None, max_length=CAFE_NAME_MAX_LENGTH)
    address: Optional[str] = Field(None, max_length=CAFE_ADDRESS_MAX_LENGTH)
    phone: Optional[str] = Field(None, max_length=CAFE_PHONE_MAX_LENGTH)
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers: Optional[List[int]] = None

    @validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Проверка, что название не пустое (если передано)."""
        if v is not None and not v.strip():
            raise ValueError("Название кафе не может быть пустым")
        return v.strip() if v is not None else v

    @validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Проверка формата телефона (если передано)."""
        if v is None:
            return v
        v_clean = (
            v.replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )
        if not v_clean.isdigit():
            raise ValueError("Телефон должен содержать только цифры")
        if len(v_clean) not in (10, 11):
            raise ValueError("Телефон должен содержать 10 или 11 цифр")
        if v_clean.startswith("8"):
            v_clean = "7" + v_clean[1:]
        elif not v_clean.startswith("7"):
            raise ValueError("Телефон должен начинаться с 7 или 8")
        return v_clean

    @validator("photo_id")
    @classmethod
    def validate_photo_id(cls, v: Optional[UUID]) -> Optional[UUID]:
        """Проверка корректности UUID для photo_id (если передано)."""
        if v is None:
            return v
        try:
            UUID(str(v))
        except ValueError:
            raise ValueError("photo_id должен быть корректным UUID")
        return v


class CafeRead(CafeBase):
    """Схема для чтения/списка кафе."""

    id: int
    created_at: str
    updated_at: str
    active: bool

    class Config:
        """Конфигурация Pydantic для работы с ORM."""

        from_attributes = True


class CafeInDB(CafeRead):
    """Схема для внутренних операций."""
