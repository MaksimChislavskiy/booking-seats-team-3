from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.enum import BookingStatus


class UserRead(BaseModel):
    """Пользователь (краткая информация)."""

    id: int
    username: str
    email: str
    phone: Optional[str]
    tg_id: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class CafeRead(BaseModel):
    """Кафе."""

    id: int
    name: str
    address: str
    phone: str
    description: Optional[str]
    photo_id: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class TableRead(BaseModel):
    """Стол."""

    id: int
    description: Optional[str]
    seat_number: int

    model_config = ConfigDict(from_attributes=True)


class SlotRead(BaseModel):
    """Временной слот."""

    id: int
    start_time: time
    end_time: time
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class TableSlotRead(BaseModel):
    """Связка стол + слот."""

    id: int
    table: TableRead
    slot: SlotRead

    model_config = ConfigDict(from_attributes=True)


class BookingRead(BaseModel):
    """Бронирование."""

    id: int
    user: UserRead
    cafe: CafeRead
    tables_slots: List[TableSlotRead]
    guest_number: int
    note: Optional[str]
    status: BookingStatus
    booking_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TableSlotCreate(BaseModel):
    """Связка стол + слот для создания/обновления бронирования."""

    table_id: int
    slot_id: int


class BookingCreate(BaseModel):
    """Схема для создания нового бронирования."""

    cafe_id: int
    tables_slots: List[TableSlotCreate]
    guest_number: int
    note: Optional[str] = None
    booking_date: date


class BookingUpdate(BaseModel):
    """Схема для обновления бронирования (PATCH)."""

    cafe_id: Optional[int] = None
    tables_slots: Optional[List[TableSlotCreate]] = None
    guest_number: Optional[int] = None
    note: Optional[str] = None
    status: Optional[BookingStatus] = None
    booking_date: Optional[date] = None
    is_active: Optional[bool] = None
