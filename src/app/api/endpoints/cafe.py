from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.responses import (
    BAD_REQUEST,
    CREATED,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.crud import cafe_crud
from app.models import User
from app.models.enum import UserRole
from app.schemas import CafeCreate, CafeInfo, CafeUpdate
from app.services.auth import (
    current_active_user,
    current_admin,
    current_admin_or_manager,
)
from app.services.cafe import cafe_service
from app.services.permissions import can_manage_cafe

router = APIRouter()


@router.get(
    '/',
    response_model=list[CafeInfo],
    summary='Получение списка кафе',
    description=(
        'Возвращает список кафе с учётом роли пользователя:\n'
        '- Администратор может получать все кафе (включая неактивные).\n'
        '- Менеджер видит все активные кафе и своё кафе.\n'
        '- Пользователь видит только активные кафе.'
    ),
    responses={
        **CREATED,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def read_list(
    user: User = Depends(current_active_user),
    show_all: bool = Query(
        False,
        description=(
            'Показывать все кафе или нет. '
            'По умолчанию показывает только активные кафе'
        ),
    ),
    session: AsyncSession = Depends(get_async_session),
) -> list[CafeInfo]:
    """Возвращает список кафе, доступных текущему пользователю.

    Args:
        show_all: Флаг отображения неактивных кафе
            (работает только для администраторов).
        user: Текущий аутентифицированный пользователь.
        session: Асинхронная сессия SQLAlchemy.

    Returns:
        Список объектов CafeInfo.

    """
    return await cafe_service.get_cafes_for_user(user, show_all, session)


@router.post(
    '/',
    response_model=CafeInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового кафе',
    description='Создаёт новое кафе. Только для администраторов и менеджеров.',
    responses={
        **CREATED,
        **BAD_REQUEST,
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
    dependencies=[Depends(current_admin)],
)
async def create(
    cafe_in: CafeCreate,
    session: AsyncSession = Depends(get_async_session),
) -> CafeInfo:
    """Создаёт новое кафе."""  # FIXME: Улучшить.
    return await cafe_service.create_cafe(cafe_in, session)


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Получение информации о кафе по ID',
    description=(
        'Возвращает кафе по идентификатору с учётом роли пользователя:\n'
        '- Администратор может получить любое кафе (включая неактивное).\n'
        '- Менеджер может получить активное кафе и своё кафе.\n'
        '- Пользователь может получить только активное кафе.'
    ),
    responses={
        **CREATED,
        **BAD_REQUEST,
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def read_cafe(
    cafe_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> CafeInfo:
    """Возвращает кафе по ID, если пользователь имеет доступ.

    Args:
        cafe_id: Идентификатор кафе.
        user: Текущий аутентифицированный пользователь.
        session: Асинхронная сессия SQLAlchemy.

    Returns:
        Объект CafeInfo.

    """
    return await cafe_service.get_cafe_by_id_for_user(cafe_id, user, session)


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Обновление информации о кафе по ID',
    description=(
        'Частичное обновление данных кафе. '
        'Только для администраторов и менеджеров.'
    ),  # FIXME: Обновить описание
    responses={
        **CREATED,
        **BAD_REQUEST,
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
    dependencies=[Depends(current_admin_or_manager)],
)
async def update(
    cafe_id: int,
    cafe_in: CafeUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> CafeInfo:
    """Обновляет данные кафе."""
    return await cafe_service.update_cafe(cafe_id, cafe_in, session)


# TODO: Добавить soft-delete
