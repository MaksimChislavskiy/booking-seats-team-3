from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (MAX_LENGTH_USER_EMAIL,
                                MAX_LENGTH_USER_PASSWORD_HASH,
                                MAX_LENGTH_USER_PHONE, MAX_LENGTH_USER_TG_ID,
                                MAX_LENGTH_USER_USERNAME, ROLE_ADMIN,
                                ROLE_MANAGER, ROLE_USER)
from app.core.db import Base
from app.models import AuditMixin

if TYPE_CHECKING:
    from app.models import Cafe


class UserRole(StrEnum):
    """Роли пользователей.

    Используется для ограничения допустимых значений роли пользователя.
    """

    ADMIN = ROLE_ADMIN
    MANAGER = ROLE_MANAGER
    USER = ROLE_USER


class User(Base, AuditMixin):
    """Модель пользователя.

    Представляет учетную запись пользователя и содержит основные
    идентификационные данные, а также роль доступа.

    Пользователь должен иметь хотя бы один способ связи:
    электронную почту или номер телефона.
    """

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
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole,
            name='user_role_enum',
        ),
        nullable=False,
    )
    cafe: Mapped['Cafe'] = relationship(
        'Cafe',
        secondary='cafe_managers',
        back_populates='managers',
        lazy='selectin',
    )
    # TODO: Добавить нужные relationship в будущем

    __table_args__ = (
        CheckConstraint(
            '(email IS NOT NULL) OR (phone IS NOT NULL)',
            name='check_user_email_or_phone_required',
        ),
    )

    def __repr__(self) -> str:
        return (
            f'<User id={self.id}, '
            f'username={self.username}, '
            f'email={self.email}, '
            f'phone={self.phone}>'
        )

    def __str__(self) -> str:
        return self.username
