from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.app.schemas.table import TableRead
from src.app.schemas.user import UserRead


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


class BookingCreate(BookingBase):
    """Схема для создания бронирования."""

    model_config = ConfigDict(extra='forbid')

    table_id: int = Field(
        ...,
        description='ID стола',
    )

    @field_validator('booking_date')
    @classmethod
    def booking_date_not_past(cls, value: date) -> date:
        """Проверяет, что дата бронирования не в прошлом."""
        if value < date.today():
            raise ValueError('Нельзя бронировать на прошедшую дату')
        return value


class BookingUpdate(BaseModel):
    """Схема для частичного обновления бронирования."""

    model_config = ConfigDict(extra='forbid')

    booking_date: date | None = Field(None, description='Дата бронирования')
    note: str | None = Field(None, description='Примечание к бронированию')
    table_id: int | None = Field(None, description='ID стола')

    @field_validator('booking_date')
    @classmethod
    def booking_date_not_past(cls, value: date | None) -> date | None:
        """Проверяет, что дата бронирования не в прошлом (если передано)."""
        if value is not None and value < date.today():
            raise ValueError('Нельзя изменить дату на прошедшую')
        return value


class BookingInfo(BookingBase):
    """Схема для чтения информации о бронировании."""

    id: int
    user: UserRead
    table: TableRead
    status: str = Field(..., description='Статус бронирования')
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
