from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_async_session
from app.core.security import verify_password
from app.crud import user_crud
from app.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')


def create_access_token(
    payload: Mapping[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Создаёт JWT access-токен.

    В токен добавляется поле `exp`, определяющее время его истечения.
    Остальные данные передаются через payload (например, `sub`).

    Args:
        payload: Данные, которые будут закодированы в JWT.
            Обычно содержит идентификатор пользователя (`sub`).
        expires_delta: Время жизни токена. Если не указано,
            используется значение по умолчанию из конфигурации.

    Returns:
        JWT access-токен в виде строки.

    """
    to_encode = dict(payload)

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode['exp'] = expire

    return jwt.encode(
        payload=to_encode,
        key=settings.secret_key,
        algorithm=settings.algorithm,
    )


async def authenticate_user(
    login: str,
    password: str,
    session: AsyncSession,
) -> User | None:
    """Аутентифицирует пользователя по логину и паролю.

    Проверяет существование пользователя и корректность пароля.
    Не выбрасывает исключений — возвращает None при ошибке,
    чтобы не раскрывать детали аутентификации.

    Args:
        login: Логин пользователя (email или телефон).
        password: Пароль в открытом виде.
        session: Асинхронная сессия базы данных.

    Returns:
        Объект User при успешной аутентификации или None.

    """
    user = await user_crud.get_by_email_or_phone(login, session)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """Возвращает текущего аутентифицированного пользователя.

    Извлекает access-токен из заголовка Authorization,
    валидирует его и загружает пользователя из базы данных.

    Args:
        token: JWT access-токен из заголовка Authorization.
        session: Асинхронная сессия базы данных.

    Returns:
        Текущий пользователь.

    Raises:
        HTTPException: 401, если токен невалиден, истёк
            или пользователь не найден.

    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Ошибка аутентификации',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id_str: str | None = payload.get('sub')
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (InvalidTokenError, ValueError):
        raise credentials_exception

    user = await user_crud.get_by_id(user_id, session)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Возвращает текущего активного пользователя.

    Используется как dependency для эндпоинтов,
    доступных только активным пользователям.

    Args:
        user: Пользователь, полученный из access-токена.

    Returns:
        Активный пользователь.

    Raises:
        HTTPException: 403, если пользователь неактивен.

    """
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Пользователь неактивен',
        )
    return user


def require_roles(*roles: UserRole) -> Callable[..., User]:
    """Factory-функция для проверки ролей пользователя.

    Принимает одну или несколько допустимых ролей и возвращает
    dependency-функцию, которая:
    - получает текущего активного пользователя
    - проверяет, что его роль входит в список допустимых
    - возвращает пользователя при успешной проверке

    Используется в Depends(...) для ограничения доступа
    к эндпоинтам по ролям.

    Args:
        *roles: Допустимые роли пользователя (UserRole).

    Returns:
        Dependency-функция, возвращающая User.

    Raises:
        HTTPException: 403, если роль пользователя недопустима.

    """

    def dependency(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Недостаточно прав доступа',
            )
        return user

    return dependency


current_active_user = get_current_active_user
current_admin = require_roles(UserRole.ADMIN)
current_admin_or_manager = require_roles(UserRole.ADMIN, UserRole.MANAGER)
