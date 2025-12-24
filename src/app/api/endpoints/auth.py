from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_async_session
from app.models import User
from app.schemas.auth import AuthData, AuthToken
from app.schemas.user import UserInfo
from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
)

router = APIRouter()


@router.post(
    '/login',
    response_model=AuthToken,
    summary='Получение токена авторизации',
    description='Возвращает токен для последующей авторизации пользователя.',
)
async def login(
    data: AuthData,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AuthToken:
    """Аутентифицирует пользователя и возвращает access-токен.

    Endpoint принимает логин (email или телефон) и пароль,
    проверяет корректность учетных данных и, в случае успеха,
    возвращает JWT-токен для последующих авторизованных запросов.

    Args:
        data: Данные для авторизации (логин и пароль).
        session: Асинхронная сессия базы данных.

    Returns:
        Объект AuthToken с access-токеном и типом токена.

    Raises:
        HTTPException: 401, если логин или пароль неверны.

    """
    user = await authenticate_user(
        login=data.login,
        password=data.password,
        session=session,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Неверный логин или пароль',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes,
    )
    access_token = create_access_token(
        payload={'sub': str(user.id)},
        expires_delta=access_token_expires,
    )
    return AuthToken(access_token=access_token, token_type='bearer')


@router.get(
    '/users/me/',
    response_model=UserInfo,
    summary='Получение данных текущего пользователя',
)
async def me(
    user: Annotated[User, Depends(get_current_active_user)],
) -> UserInfo:
    """Пример для вызова информации о пользователе."""
    return user
