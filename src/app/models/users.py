from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_HASH_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
)
from app.core.db import Base
from app.models.base import AuditMixin


class User(Base, AuditMixin):
    """Модель пользователя.

    Содержит данные учетной записи.
    """

    username: Mapped[str] = mapped_column(
        String(USERNAME_MAX_LENGTH),
        unique=True,
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(EMAIL_MAX_LENGTH),
        unique=True,
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(PHONE_MAX_LENGTH),
        unique=True,
        nullable=True,
    )

    tg_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(PASSWORD_HASH_MAX_LENGTH),
        nullable=False,
    )
