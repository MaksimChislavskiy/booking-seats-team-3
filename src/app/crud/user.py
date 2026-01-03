from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.crud.base import CRUDBase
from app.models import User
from app.schemas import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD для работы с пользователями.

    Содержит методы выборки пользователей по уникальным полям
    (username, email, phone). Не содержит HTTP или бизнес-логики.
    """

    async def _get_by_field(
        self,
        field: InstrumentedAttribute,
        value: Any,
        session: AsyncSession,
    ) -> User | None:
        """Возвращает пользователя по значению указанного поля.

        Приватный универсальный метод для выборки пользователя
        по уникальному полю модели User.

        Args:
            field: Атрибут модели User (например, User.email).
            value: Значение поля для поиска.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Пользователь или None, если запись не найдена.

        """
        stmt = select(User).where(field == value)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(
        self,
        username: str,
        session: AsyncSession,
    ) -> User | None:
        """Возвращает пользователя по username."""
        return await self._get_by_field(User.username, username, session)

    async def get_by_email(
        self,
        email: str,
        session: AsyncSession,
    ) -> User | None:
        """Возвращает пользователя по email."""
        return await self._get_by_field(User.email, email, session)

    async def get_by_phone(
        self,
        phone: str,
        session: AsyncSession,
    ) -> User | None:
        """Возвращает пользователя по номеру телефона."""
        return await self._get_by_field(User.phone, phone, session)

    async def get_by_tg_id(
        self,
        tg_id: str,
        session: AsyncSession,
    ) -> User | None:
        """Возвращает пользователя по Telegram ID."""
        return await self._get_by_field(User.tg_id, tg_id, session)


user_crud = CRUDUser(User)
