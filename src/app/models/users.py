from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import (
    MAX_LENGTH_USER_EMAIL,
    MAX_LENGTH_USER_PASSWORD_HASH,
    MAX_LENGTH_USER_PHONE,
    MAX_LENGTH_USER_TG_ID,
    MAX_LENGTH_USER_USERNAME,
)
from app.core.db import Base
from app.models.base import AuditMixin


class User(Base, AuditMixin):
    """Модель пользователя.

    Содержит данные учетной записи.
    """

    __table_args__ = (
        CheckConstraint(
            "(email IS NOT NULL) OR (phone IS NOT NULL)",
            name="check_user_email_or_phone_required",
        ),
    )

    username: Mapped[str] = mapped_column(
        String(MAX_LENGTH_USER_USERNAME),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(MAX_LENGTH_USER_EMAIL),
        unique=True,
        index=True,
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(MAX_LENGTH_USER_PHONE),
        unique=True,
        nullable=True,
    )

    tg_id: Mapped[str | None] = mapped_column(
        String(MAX_LENGTH_USER_TG_ID),
        unique=True,
        nullable=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(MAX_LENGTH_USER_PASSWORD_HASH),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"

    def __str__(self) -> str:
        return self.username
