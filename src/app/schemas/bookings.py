from datetime import date
from typing import Optional

from pydantic import BaseModel
from app.models.enum import BookingStatus


class BookingBase(BaseModel):
    user_id: int
    cafe_id: int
    table_id: int
    slot_id: int
    date: date
    note: Optional[str] = None


class BookingCreate(BookingBase):  # для POST
    pass  # при создании статус всегда pending


class BookingUpdate(BaseModel):  # для PATCH/PUT
    status: Optional[BookingStatus] = None
    note: Optional[str] = None


class BookingRead(BookingBase):  # для ответа с id и статусом
    id: int
    status: BookingStatus

    class Config:
        orm_mode = True
