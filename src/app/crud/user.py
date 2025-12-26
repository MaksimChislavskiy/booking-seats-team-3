from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import User
from app.schemas import UserCreate, UserUpdate


class UserCRUD(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD для работы с пользователями.

    Содержит методы выборки пользователей по уникальным полям
    (username, email, phone). Не содержит HTTP или бизнес-логики.
    """

    async def get_by_username(
        self,
        username: str,
        session: AsyncSession,
    ) -> User | None:
        """Возвращает пользователя по username.

        Args:
            username: Уникальное имя пользователя.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Пользователь или None, если не найден.

        """
        result = await session.execute(
            select(User).where(User.username == username),
        )
        return result.scalar_one_or_none()

    async def get_by_email_or_phone(
        self,
        value: str,
        session: AsyncSession,
    ) -> User | None:
        """Возвращает пользователя по email или phone.

        Args:
            value: Email или номер телефона.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Пользователь или None, если не найден.

        """
        result = await session.execute(
            select(User).where(
                or_(
                    User.email == value,
                    User.phone == value,
                ),
            ),
        )
        return result.scalar_one_or_none()


user_crud = UserCRUD(User)
