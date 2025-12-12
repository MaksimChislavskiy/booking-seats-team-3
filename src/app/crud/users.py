from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.users import User
from app.schemas.users import UserCreate, UserUpdate


class UserCRUD:
    """CRUD-класс для работы с пользователями.

    Содержит операции получения, создания, обновления
    и деактивации пользователей.
    """

    @staticmethod
    async def get_by_id(user_id: int, session: AsyncSession) -> Optional[User]:
        """Получает пользователя по его ID.

        Возвращает объект пользователя или None, если он не найден.
        """
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(
        email: str,
        session: AsyncSession,
    ) -> Optional[User]:
        """Получает пользователя по email.

        Используется при проверках уникальности и аутентификации.
        """
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(user_in: UserCreate, session: AsyncSession) -> User:
        """Создает нового пользователя.

        Пароль автоматически хешируется и сохраняется
        в виде password_hash.
        """
        hashed_password = get_password_hash(user_in.password)

        new_user = User(
            username=user_in.username,
            email=user_in.email,
            phone=user_in.phone,
            password_hash=hashed_password,
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    @staticmethod
    async def update(
        user: User,
        user_in: UserUpdate,
        session: AsyncSession,
    ) -> User:
        """Обновляет данные пользователя.

        Обновляются только переданные поля.
        При передаче нового пароля он хешируется автоматически.
        """
        for field, value in user_in.model_dump(exclude_unset=True).items():
            if field == "password":
                value = get_password_hash(value)
                setattr(user, "password_hash", value)
            else:
                setattr(user, field, value)

        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def delete(user: User, session: AsyncSession) -> User:
        """Деактивирует пользователя.

        Мягкое удаление — пользователь остаётся в базе,
        но помечается как неактивный.
        """
        user.active = False
        await session.commit()
        return user
