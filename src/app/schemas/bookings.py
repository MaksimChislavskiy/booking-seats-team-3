from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enum import BookingStatus


class BookingBase(BaseModel):
    """Базовая схема бронирования."""

    cafe_id: int
    table_slot_id: int
    date: date
    note: Optional[str] = None


class BookingCreate(BookingBase):
    """Схема для создания бронирования (POST)."""

    pass  # статус всегда pending


class BookingUpdate(BaseModel):
    """Схема для обновления бронирования (PATCH)."""

    status: Optional[BookingStatus] = None
    note: Optional[str] = None


class BookingRead(BookingBase):
    """Схема бронирования для ответа (GET)."""

    id: int
    user_id: int
    status: BookingStatus

    model_config = ConfigDict(from_attributes=True)
