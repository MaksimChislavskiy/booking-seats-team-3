from typing import TYPE_CHECKING, List

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
from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models import Slot, Table, User


class Cafe(AuditMixin, Base):
    """Модель кафе.

    Содержит информацию о кафе: название, адрес, контакты, менеджеры.
    """

    __table_args__ = (
        UniqueConstraint('name', 'address', name='uq_cafe_name_address')
    )

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
        ForeignKey('files.id', ondelete='SET NULL'),
        nullable=True,
    )
    # TODO: Добавить relationship для booking, когда будет создана модель
    # bookings: Mapped[List["Booking"]] = relationship(
    #     "Booking",
    #     back_populates="cafe",
    #     cascade="all, delete-orphan",
    # )
    managers: Mapped[List['User']] = relationship(
        'User',
        back_populates='managed_cafe',
    )
    tables: Mapped[List['Table']] = relationship(
        'Table',
        back_populates='cafe',
        cascade='all, delete-orphan',
    )
    slots: Mapped[List['Slot']] = relationship(
        'Slot',
        back_populates='cafe',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return (
            f'Cafe(id={self.id}, name="{self.name}", '
            f'address="{self.address}")'
        )

    def __str__(self) -> str:
        return f'Кафе "{self.name}" (адрес: {self.address})'
