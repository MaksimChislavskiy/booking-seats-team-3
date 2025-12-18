from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import MAX_SEATS_NUMBER, MIN_SEATS_NUMBER
from app.core.db import Base
from app.models import Cafe


class Table(Base):
    """Информация о столах для бронирования."""

    seat_number: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
        doc='Количество мест за столом.',
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc='Описание, характеристики стола.',
    )

    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafe.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        doc='Идентификатор кафе.',
    )

    cafe: Mapped['Cafe'] = relationship(
        'Cafe',
        back_populates='tables',
        doc='Кафе, к которому относится стол.',
    )

    __table_args__ = (
        CheckConstraint(
            f'seat_number BETWEEN {MIN_SEATS_NUMBER} AND {MAX_SEATS_NUMBER}',
            name='check_seat_number_range',
        ),
    )

    def __repr__(self) -> str:
        return (
            f'Table id={self.id}, '
            f'seat_number={self.seat_number}, '
            f'cafe_id={self.cafe_id}'
        )

    def __str__(self) -> str:
        return f'Стол {self.id} в кафе {self.cafe_id}'
