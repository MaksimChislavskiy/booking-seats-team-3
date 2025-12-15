"""Чтобы потом не забыть про relationship для Cafe. Немного опишу модель."""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship

from app.core.db import Base
from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.cafes import Cafe


class User(AuditMixin, Base):
    """Заглушка."""

    # остальные поля...

    cafe: Mapped[Cafe | None] = relationship(
        'Cafe',
        secondary='cafe_managers',
        back_populates='managers',
        lazy='selectin',
    )
