import datetime

from sqlalchemy import Date, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.db import Base
from app.models.base import AuditMixin
from app.models.enum import BookingStatus


class TableSlot(Base):
    """
    Связка стола и временного слота.
    """

    id: Mapped[int] = mapped_column(primary_key=True)

    table_id: Mapped[int] = mapped_column(
        ForeignKey('table.id'),
        nullable=False,
    )

    slot_id: Mapped[int] = mapped_column(
        ForeignKey('slot.id'),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            'table_id',
            'slot_id',
            name='uq_table_slot',
        ),
    )

    def __str__(self) -> str:
        return f'Стол {self.table_id} — слот {self.slot_id}'


class Booking(Base, AuditMixin):
    """
    Бронирование столов в ресторане.
    """

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id'),
        nullable=False,
    )

    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafe.id'),
        nullable=False,
    )

    table_slot_id: Mapped[int] = mapped_column(
        ForeignKey('tableslot.id'),
        nullable=False,
    )

    date: Mapped[datetime.date] = mapped_column(
        Date,
        nullable=False,
    )

    @validates('date')
    def validate_date(self, key: str, value: datetime.date) -> datetime.date:
        """Проверка, что дата бронирования не в прошлом."""
        if value < datetime.date.today():
            raise ValueError('Нельзя создать бронирование на прошедшую дату')
        return value

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name='booking_status'),
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint(
            'table_slot_id',
            'date',
            name='uq_booking_table_slot_date',
        ),
    )

    def __repr__(self) -> str:
        return (
            f'Booking id={self.id} '
            f'user_id={self.user_id} '
            f'cafe_id={self.cafe_id} '
            f'table_id={self.table_id} '
            f'slot_id={self.slot_id} '
            f'date={self.date} '
            f'status={self.status}'
        )

    def __str__(self) -> str:
        return f'Бронирование №{self.id} - {self.date}'
