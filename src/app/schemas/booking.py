from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.app.schemas.cafe import CafeShortInfo
from src.app.schemas.table import TableShortInfo
from src.app.schemas.user import UserShortInfo


class BookingStatus(str, Enum):
    """Статусы бронирования."""

    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'


class BookingBase(BaseModel):
    """Общие поля для всех схем Booking."""

    booking_date: date = Field(
        ...,
        description='Дата бронирования',
    )
    note: str | None = Field(
        None,
        description='Примечание к бронированию',
    )
    guest_number: int = Field(
        ...,
        ge=1,
        description='Количество гостей',
    )


class BookingCreate(BookingBase):
    """Схема для создания бронирования."""

    cafe_id: int = Field(
        ...,
        description='ID кафе',
    )
    table_id: int = Field(
        ...,
        description='ID стола',
    )
    slot_id: int = Field(
        ...,
        description='ID временного слота',
    )
    status: BookingStatus = Field(
        BookingStatus.PENDING,
        description='Статус бронирования',
    )

    model_config = ConfigDict(extra='forbid')

    @field_validator('booking_date')
    @classmethod
    def check_booking_date_not_past(cls, value: date) -> date:
        """Проверяет, что дата бронирования не в прошлом."""
        if value < date.today():
            raise ValueError('Нельзя бронировать на прошедшую дату')
        return value


class BookingUpdate(BaseModel):
    """Схема для частичного обновления бронирования."""

    booking_date: date | None = Field(None, description='Дата бронирования')
    note: str | None = Field(None, description='Примечание к бронированию')
    guest_number: int | None = Field(None, description='Количество гостей')
    table_id: int | None = Field(None, description='ID стола')
    slot_id: int | None = Field(None, description='ID временного слота')
    status: BookingStatus | None = Field(
        None,
        description='Статус бронирования',
    )

    model_config = ConfigDict(extra='forbid')

    @field_validator('booking_date')
    @classmethod
    def check_booking_date_not_past(cls, value: date | None) -> date | None:
        """Проверяет, что дата бронирования не в прошлом (если передано)."""
        if value is not None and value < date.today():
            raise ValueError('Нельзя изменить дату на прошедшую')
        return value


class BookingInfo(BookingBase):
    """Схема для чтения информации о бронировании."""

    id: int
    user: UserShortInfo
    cafe: CafeShortInfo
    table: TableShortInfo
    slot_id: int
    status: BookingStatus
    guest_number: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
