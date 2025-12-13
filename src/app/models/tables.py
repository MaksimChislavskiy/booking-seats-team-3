from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.constants import MAX_SEATS_NUMBER, MIN_SEATS_NUMBER
from core.db import Base
from models.base import AuditMixin


class Table(Base, AuditMixin):
    """Информация о столах для бронирования."""

    seat_number: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
        doc='Количество мест за столом.',
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Описание, характеристики стола.',
    )

    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafes.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc='Идентификатор кафе.',
    )

    cafe: Mapped['Cafe'] = relationship(  # noqa: F821
        'Cafe',
        back_populates='tables',
        doc='Все характеристики кафе.',
    )

    __table_args__ = (
        CheckConstraint(
            f'seat_number >= {MIN_SEATS_NUMBER}',
            name='check_min_seats'),
        CheckConstraint(
            f'seat_number <= {MAX_SEATS_NUMBER}',
            name='check_max_seats'),
    )

    def __str__(self) -> str:
        return f'Стол {self.id} в кафе {self.cafe_id}'
