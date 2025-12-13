from typing import List, Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    CAFE_ADDRESS_MAX_LENGTH,
    CAFE_NAME_MAX_LENGTH,
    CAFE_PHONE_MAX_LENGTH,
)
from app.core.db import Base
from app.models.base import AuditMixin


class Cafe(Base, AuditMixin):
    """Модель кафе.

    Содержит информацию о кафе: название, адрес, контакты, менеджеры.
    """

    name: Mapped[str] = mapped_column(
        String(CAFE_NAME_MAX_LENGTH),
        nullable=False,
        index=True,
    )
    address: Mapped[str] = mapped_column(
        String(CAFE_ADDRESS_MAX_LENGTH),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(CAFE_PHONE_MAX_LENGTH),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,  # Для длинных описаний, без ограничения длины
        nullable=True,
    )
    photo: Mapped[Optional[str]] = mapped_column(
        String(36),  # UUID храним как строку (36 символов)
        nullable=True,
    )
    managers_id: Mapped[List[int]] = mapped_column(
        ARRAY(Integer),  # Массив ID менеджеров (int)
        nullable=False,
        default=[],  # Пустой массив по умолчанию
    )
    # Связи
    tables: Mapped[List["Table"]] = relationship(  # noqa: F821
        "Table",
        back_populates="cafe",
        cascade="all, delete-orphan",
    )
    slots: Mapped[List["Slot"]] = relationship(  # noqa: F821
        "Slot",
        back_populates="cafe",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Cafe(id={self.id}, name={self.name})"
