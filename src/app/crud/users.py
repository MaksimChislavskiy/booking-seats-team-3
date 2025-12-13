from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.crud.base import BaseCRUD
from app.models.users import User
from app.schemas.users import UserCreate, UserUpdate


class UserCRUD(BaseCRUD):
    """CRUD-класс для работы с пользователями."""

    def __init__(self) -> None:
        """Инициализирует CRUD для модели User."""
        super().__init__(User)

    async def get_by_email(
        self,
        email: str,
        session: AsyncSession,
    ) -> Optional[User]:
        """Возвращает пользователя по email."""
        result = await session.execute(
            select(User).where(User.email == email),
        )
        return result.scalar_one_or_none()

    async def get_by_phone(
        self,
        phone: str,
        session: AsyncSession,
    ) -> Optional[User]:
        """Возвращает пользователя по номеру телефона."""
        result = await session.execute(
            select(User).where(User.phone == phone),
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_in: UserCreate,
        session: AsyncSession,
    ) -> User:
        """Создает нового пользователя с проверками уникальности."""
        # Валидация уникальности email
        if user_in.email:
            if await self.get_by_email(user_in.email, session):
                raise ValueError("Пользователь с таким email уже существует")

        #  Валидация уникальности phone
        if user_in.phone:
            if await self.get_by_phone(user_in.phone, session):
                raise ValueError(
                    "Пользователь с таким номером телефона уже существует",
                )

        user = User(
            username=user_in.username,
            email=user_in.email,
            phone=user_in.phone,
            password_hash=get_password_hash(user_in.password),
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def update(
        self,
        user: User,
        user_in: UserUpdate,
        session: AsyncSession,
    ) -> User:
        """Обновляет данные пользователя с проверками уникальности."""
        data = user_in.model_dump(exclude_unset=True)

        # Проверка email при изменении
        if "email" in data and data["email"] != user.email:
            if await self.get_by_email(data["email"], session):
                raise ValueError("Пользователь с таким email уже существует")

        # Проверка phone при изменении
        if "phone" in data and data["phone"] != user.phone:
            if await self.get_by_phone(data["phone"], session):
                raise ValueError(
                    "Пользователь с таким номером телефона уже существует",
                )

        for field, value in data.items():
            if field == "password":
                user.password_hash = get_password_hash(value)
            else:
                setattr(user, field, value)

        await session.commit()
        await session.refresh(user)
        return user
