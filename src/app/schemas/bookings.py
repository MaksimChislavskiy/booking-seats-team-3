from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.models.enum import BookingStatus


class BookingBase(BaseModel):
    """Базовая схема бронирования."""

    user_id: int
    cafe_id: int
    table_id: int
    slot_id: int
    date: date
    note: Optional[str] = None


class BookingCreate(BookingBase):
    """Для создания бронирования (POST)."""

    pass  # при создании статус всегда pending


class BookingUpdate(BaseModel):
    """Для обновления бронирования (PATCH/PUT)."""

    status: Optional[BookingStatus] = None
    note: Optional[str] = None


class BookingRead(BookingBase):
    """Схема бронирования для ответа (GET)."""

    id: int
    status: BookingStatus

    class Config:
        orm_mode = True
