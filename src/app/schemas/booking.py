from datetime import date, datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import MAX_LENGTH_BOOKING_NOTE
from app.models import BookingStatus
from app.schemas.cafe import CafeShortInfo
from app.schemas.slot import TimeSlotShortInfo
from app.schemas.table import TableShortInfo
from app.schemas.user import UserShortInfo


class TableSlot(BaseModel):
    """Пара стол + временной слот."""

    table_id: int = Field(..., description='ID стола')
    slot_id: int = Field(..., description='ID временного слота')

    model_config = ConfigDict(extra='forbid')


class TableSlotInfo(BaseModel):
    """Информация о занятом столе и временном слоте в бронировании."""

    id: int = Field(..., description='ID связи стол–слот')
    table: TableShortInfo = Field(..., description='Информация о столе')
    slot: TimeSlotShortInfo = Field(..., description='Информация о слоте')

    model_config = ConfigDict(from_attributes=True)


class BookingBase(BaseModel):
    """Общие поля для всех схем бронирования."""

    note: str | None = Field(None, max_length=MAX_LENGTH_BOOKING_NOTE)
    guest_number: int = Field(..., ge=1)


class BookingDateValidationMixin(BaseModel):
    """Валидация даты бронирования (не в прошлом)."""

    booking_date: date = Field(...)

    @field_validator('booking_date')
    @classmethod
    def check_date_not_past(cls, v: date) -> date:
        """Проверяет, что дата бронирования не в прошлом."""
        if v < date.today():
            raise ValueError('Дата бронирования не может быть в прошлом')
        return v


class BookingCreate(BookingBase, BookingDateValidationMixin):
    """Схема для создания бронирования."""

    cafe_id: int = Field(..., description='ID кафе')
    tables_slots: List[TableSlot] = Field(..., min_length=1)
    status: BookingStatus = Field(default=BookingStatus.PENDING)

    model_config = ConfigDict(extra='forbid')


class BookingUpdate(BaseModel):
    """Схема для обновления бронирования."""

    note: str | None = None
    guest_number: int | None = None
    status: BookingStatus | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra='forbid')


class BookingInfo(BookingBase):
    """Полная информация о бронировании."""

    id: int = Field(...)
    user: UserShortInfo = Field(...)
    cafe: CafeShortInfo = Field(...)
    tables_slots: List[TableSlotInfo] = Field(...)
    status: BookingStatus = Field(...)
    booking_date: date = Field(...)
    is_active: bool = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    model_config = ConfigDict(from_attributes=True)
