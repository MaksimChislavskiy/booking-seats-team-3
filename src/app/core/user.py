from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi_users import (
    BaseUserManager,
    FastAPIUsers,
    IntegerIDMixin,
    InvalidPasswordException,
)
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_async_session
from app.core.security import check_password_rules
from app.models import User, UserRole


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, int], None]:
    """Создает объект для работы с БД пользователя по сессии."""
    yield SQLAlchemyUserDatabase(session, User)


bearer_transport = BearerTransport(tokenUrl='auth/login')


def get_jwt_strategy() -> JWTStrategy:
    """Создает и возвращает объект JWTStrategy.

    Используется для генерации и валидации access JWT-токенов,
    передаваемых через Bearer Authorization header.
    """
    return JWTStrategy(
        secret=settings.secret,
        lifetime_seconds=settings.access_token_expire_seconds,
    )


auth_backend = AuthenticationBackend(
    name='jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """Менеджер пользователей для fastapi-users."""

    async def validate_password(
        self,
        password: str,
        user: User | None = None,
    ) -> None:
        """Валидирует пароль на соответствие установленным правилам."""
        reason = check_password_rules(password, getattr(user, 'email', None))
        if reason:
            raise InvalidPasswordException(reason=reason)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, int] = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    """Dependency для получения UserManager."""
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user(active=True)


def current_admin(
    user: User = Depends(current_user),
) -> User:
    """Dependency: доступ только для администратора."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав доступа',
        )
    return user


def current_manager_or_admin(
    user: User = Depends(current_user),
) -> User:
    """Dependency: доступ для менеджера или администратора."""
    if user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав доступа',
        )
    return user
