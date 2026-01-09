from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import MAX_LENGTH_BOOKING_NOTE
from app.core.db import Base
from app.models.enum import BookingStatus

if TYPE_CHECKING:
    from app.models.cafe import Cafe
    from app.models.slot import Slot
    from app.models.table import Table
    from app.models.user import User


class TableSlotBooking(Base):
    """Связь бронирования, стола и слота."""

    table_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('table.id', ondelete='RESTRICT'),
        nullable=False,
    )
    slot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('slot.id', ondelete='RESTRICT'),
        nullable=False,
    )
    booking_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('booking.id', ondelete='RESTRICT'),
        nullable=False,
    )

    booking: Mapped['Booking'] = relationship(
        'Booking',
        back_populates='tables_slots',
    )
    table: Mapped['Table'] = relationship('Table', lazy='selectin')
    slot: Mapped['Slot'] = relationship('Slot', lazy='selectin')

    __table_args__ = (
        UniqueConstraint(
            'table_id',
            'slot_id',
            'booking_id',
            name='uq_table_slot_booking',
        ),
    )


class Booking(Base):
    """Бронирование столов в кафе."""

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('user.id', ondelete='RESTRICT'),
        nullable=False,
    )
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafe.id', ondelete='RESTRICT'),
        nullable=False,
    )
    guest_number: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(
        String(MAX_LENGTH_BOOKING_NOTE),
        nullable=True,
    )
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, name='booking_status_enum'),
        nullable=False,
        default=BookingStatus.PENDING,
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    user: Mapped['User'] = relationship('User', lazy='selectin')
    cafe: Mapped['Cafe'] = relationship('Cafe', lazy='selectin')

    tables_slots: Mapped[list['TableSlotBooking']] = relationship(
        'TableSlotBooking',
        back_populates='booking',
        lazy='selectin',
    )

    __table_args__ = (
        CheckConstraint(
            'booking_date >= CURRENT_DATE',
            name='check_booking_date_not_past',
        ),
    )
