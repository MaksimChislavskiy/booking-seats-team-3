from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.exceptions import UserNotFoundError
from app.core.responses import (
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    USER_CONFLICT_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.crud.user import user_crud
from app.models import User
from app.schemas import UserCreate, UserInfo, UserUpdate
from app.services.auth import (
    current_active_user,
    current_admin_or_manager,
)
from app.services.user import user_service

router = APIRouter()


@router.get(
    '/',
    response_model=list[UserInfo],
    summary='Получение списка пользователей',
    dependencies=[Depends(current_admin_or_manager)],
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
    },
)
async def get_users_list(
    session: AsyncSession = Depends(get_async_session),
) -> list[UserInfo]:
    """Возвращает информацию о всех пользователях.

    Только для администраторов или менеджеров.
    """
    return await user_crud.get_multi(session=session)


@router.post(
    '/',
    response_model=UserInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация нового пользователя',
    description='Создает нового пользователя с указанными данными.',
    responses={
        **USER_CONFLICT_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def create_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_async_session),
) -> UserInfo:
    """Создает нового пользователя.

    - принимает данные регистрации
    - хэширует пароль
    - задаёт роль по умолчанию
    - сохраняет пользователя в БД
    """
    return await user_service.create_user(
        user_in=user_in,
        session=session,
    )


@router.get(
    '/me',
    response_model=UserInfo,
    summary='Получение информации о текущем пользователе',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
    },
)
async def get_me(
    user: User = Depends(current_active_user),
) -> UserInfo:
    """Возвращает информацию о текущем пользователе.

    Только для авторизованных пользователей.
    """
    return user


@router.patch(
    '/me',
    response_model=UserInfo,
    summary='Обновление информации о текущем пользователе',
    responses={
        **USER_CONFLICT_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def update_me(
    user_in: UserUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> UserInfo:
    """Возвращает обновленную информацию о пользователе.

    Только для авторизованных пользователей.
    """
    return await user_service.update_user(
        user_id=user.id,
        user_in=user_in,
        session=session,
    )


@router.get(
    '/{user_id}',
    response_model=UserInfo,
    summary='Получение пользователя по ID',
    dependencies=[Depends(current_admin_or_manager)],
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def get_user_by_id(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> UserInfo:
    """Возвращает пользователя по его ID.

    Только для администраторов или менеджеров.
    """
    user = await user_crud.get_by_id(user_id, session)
    if not user:
        raise UserNotFoundError('Пользователь не найден')
    return user


@router.patch(
    '/{user_id}',
    response_model=UserInfo,
    summary='Обновление пользователя по ID',
    dependencies=[Depends(current_admin_or_manager)],
    responses={
        **USER_CONFLICT_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> UserInfo:
    """Возвращает обновленную информацию о пользователе по его ID.

    Только для администраторов или менеджеров.
    """
    return await user_service.update_user(
        user_id=user_id,
        user_in=user_in,
        session=session,
    )


# TODO: Add deactivate_user
