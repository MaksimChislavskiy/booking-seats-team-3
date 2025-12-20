from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.app.schemas.cafe import CafeRead
from src.app.schemas.slot import SlotRead
from src.app.schemas.table import TableRead
from src.app.schemas.user import UserRead


class BookingBase(BaseModel):
    """Общие поля для всех схем Booking."""

    date: date = Field(
        ...,
        description='Дата бронирования',
    )
    note: Optional[str] = Field(
        None,
        description='Примечание к бронированию',
    )


class BookingCreate(BookingBase):
    """Схема для создания бронирования."""

    table_id: int = Field(
        ...,
        description='ID стола',
    )
    slot_id: int = Field(
        ...,
        description='ID временного слота',
    )

    @field_validator('date')
    @classmethod
    def date_not_past(cls, value: date) -> date:
        """Дата бронирования не может быть в прошлом."""
        if value < date.today():
            raise ValueError('Нельзя бронировать на прошедшую дату')
        return value


class BookingUpdate(BookingBase):
    """Схема для частичного обновления бронирования."""

    table_id: Optional[int] = Field(None, description='ID стола')
    slot_id: Optional[int] = Field(None, description='ID временного слота')

    @field_validator('date')
    @classmethod
    def date_not_past(cls, value: Optional[date]) -> Optional[date]:
        """Дата не может быть в прошлом (если передано)."""
        if value is not None and value < date.today():
            raise ValueError('Нельзя изменить дату на прошедшую')
        return value


class BookingRead(BookingBase):
    """Схема для чтения бронирования."""

    id: int
    user: UserRead
    cafe: CafeRead
    table: TableRead
    slot: SlotRead
    status: str = Field(..., description='Статус бронирования')
    created_at: datetime
    updated_at: datetime
    active: bool

    class Config:
        """Конфигурация Pydantic."""

        from_attributes = True
