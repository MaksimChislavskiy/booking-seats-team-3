from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    MAX_LENGTH_CAFE_ADDRESS,
    MAX_LENGTH_CAFE_DESCRIPTION,
    MAX_LENGTH_CAFE_NAME,
    MAX_LENGTH_CAFE_PHONE,
    MAX_LENGTH_UUID,
)
from app.core.db import Base
from app.models import AuditMixin

if TYPE_CHECKING:
    from app.models import Booking, Slot, Table, User


class Cafe(AuditMixin, Base):
    """Модель кафе.

    Представляет кафе в системе бронирования мест. Содержит информацию
    об основных параметрах кафе, связях с менеджерами, столами и слотами.

    Attributes:
        name: Название кафе.
        address: Адрес кафе.
        phone: Номер телефона кафе.
        description: Описание кафе (опционально).
        photo_id: Идентификатор фотографии кафе (опционально).
        managers: Список менеджеров кафе.
        tables: Список столов в кафе.
        slots: Список временных слотов кафе.
        booking: Список бронирований кафе.

    """

    name: Mapped[str] = mapped_column(
        String(MAX_LENGTH_CAFE_NAME),
        nullable=False,
        index=True,
    )
    address: Mapped[str] = mapped_column(
        String(MAX_LENGTH_CAFE_ADDRESS),
        nullable=False,
        index=True,
    )
    phone: Mapped[str] = mapped_column(
        String(MAX_LENGTH_CAFE_PHONE),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(MAX_LENGTH_CAFE_DESCRIPTION),
        nullable=True,
    )
    photo_id: Mapped[str | None] = mapped_column(
        String(MAX_LENGTH_UUID),
        ForeignKey('media.id', ondelete='RESTRICT'),
        nullable=True,
    )
    managers: Mapped[list['User']] = relationship(
        'User',
        secondary='cafe_managers',
        back_populates='cafe',
        lazy='selectin',
    )
    tables: Mapped[list['Table']] = relationship(
        'Table',
        back_populates='cafe',
        lazy='selectin',
    )
    slots: Mapped[list['Slot']] = relationship(
        'Slot',
        back_populates='cafe',
        lazy='selectin',
    )
    bookings: Mapped[list['Booking']] = relationship(
        'Booking',
        back_populates='cafe',
        lazy='selectin',
    )

    __table_args__ = UniqueConstraint(
        'name',
        'address',
        name='uq_cafe_name_address',
    )

    def __repr__(self) -> str:
        return (
            f'<Cafe id={self.id} name="{self.name}" address="{self.address}">'
        )

    def __str__(self) -> str:
        return f'Кафе "{self.name}" (адрес: {self.address})'
