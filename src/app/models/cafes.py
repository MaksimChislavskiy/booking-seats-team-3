from typing import List

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    MAX_LENGTH_CAFE_ADDRESS,
    MAX_LENGTH_CAFE_NAME,
    MAX_LENGTH_CAFE_PHONE,
    MAX_LENGTH_UUID,
)
from app.core.db import Base
from app.models.base import AuditMixin


class Cafe(AuditMixin, Base):
    """Модель кафе.

    Содержит информацию о кафе: название, адрес, контакты, менеджеры.
    """

    name: Mapped[str] = mapped_column(
        String(MAX_LENGTH_CAFE_NAME),
        nullable=False,
        index=True,
    )
    address: Mapped[str] = mapped_column(
        String(MAX_LENGTH_CAFE_ADDRESS),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(MAX_LENGTH_CAFE_PHONE),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    photo: Mapped[str | None] = mapped_column(
        String(MAX_LENGTH_UUID),
        nullable=True,
    )
    managers_id: Mapped[List[int]] = mapped_column(
        ARRAY(Integer),
        nullable=False,
        default=[],
    )
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
        return (
            f"Cafe(id={self.id}, name='{self.name}', "
            f"address='{self.address}')"
        )

    def __str__(self) -> str:
        return f"Кафе '{self.name}' (адрес: {self.address})"
