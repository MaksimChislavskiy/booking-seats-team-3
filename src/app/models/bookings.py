import datetime

from sqlalchemy import Date, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import AuditMixin
from app.models.enum import BookingStatus


class Booking(AuditMixin, Base):
    __tablename__ = 'bookings'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafes.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    table_id: Mapped[int] = mapped_column(
        ForeignKey('tables.id', ondelete='CASCADE'),
        nullable=False,
    )

    slot_id: Mapped[int] = mapped_column(
        ForeignKey('slots.id', ondelete='CASCADE'),
        nullable=False,
    )

    date: Mapped[datetime.date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name='booking_status'),
        nullable=False,
        default=BookingStatus.pending,
        server_default=BookingStatus.pending.value,
        index=True,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"Booking(id={self.id}, user_id={self.user_id}, "
            f"cafe_id={self.cafe_id}, "
            f"table_id={self.table_id}, slot_id={self.slot_id}, "
            f"date={self.date}, status={self.status})"
        )

    def __str__(self) -> str:
        note_str = f", note={self.note}" if self.note else ""
        return (
            f"Booking {self.id} for user {self.user_id} at cafe {self.cafe_id}, "
            f"table {self.table_id}, slot {self.slot_id} on {self.date}, status {self.status}"
            f"{note_str}"
        )
