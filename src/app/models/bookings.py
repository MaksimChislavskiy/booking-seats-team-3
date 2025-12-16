from datetime import date

from sqlalchemy import (
    CheckConstraint, Date, Enum, ForeignKey, Text, text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import AuditMixin
from app.models.enum import BookingStatus


class TableSlot(Base):
    """Связка стола и временного слота."""

    table_id: Mapped[int] = mapped_column(
        ForeignKey('table.id', ondelete='RESTRICT'),
        nullable=False,
    )

    slot_id: Mapped[int] = mapped_column(
        ForeignKey('slot.id', ondelete='RESTRICT'),
        nullable=False,
    )

    booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("booking.id", ondelete="SET NULL"),
        nullable=True,
    )

    booking: Mapped["Booking"] = relationship(
        back_populates="table_slot",
        uselist=False,
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
    """Бронирование столов в ресторане."""

    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='RESTRICT'),
        nullable=False,
    )

    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafe.id', ondelete='RESTRICT'),
        nullable=False,
    )

    table_slot_id: Mapped[int] = mapped_column(
        ForeignKey('tableslot.id', ondelete='RESTRICT'),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name='booking_status'),
        nullable=False,
        server_default=text("'pending'"),
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "date >= CURRENT_DATE",
            name="ck_booking_date_not_past",
        ),
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
            f'table_slot_id={self.table_slot_id} '
            f'date={self.date} '
            f'status={self.status}'
        )

    def __str__(self) -> str:
        return f'Бронирование №{self.id} - {self.date}'
