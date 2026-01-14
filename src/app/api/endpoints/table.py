import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_async_session
from app.core.responses import (
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.crud.table import table_crud
from app.models import Table, User, UserRole
from app.schemas import TableCreate, TableInfo, TableUpdate
from app.services.auth import current_active_user, current_admin_or_manager
from app.services.cafe import can_manage_cafe, get_cafe_or_404

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    '/{table_id}',
    response_model=TableInfo,
    summary='Получение информации о столе в кафе по ID.',
    description=(
        'Для администраторов и менеджеров этого кафе - все столы, '
        'для пользователей и остальных менеджеров - только активные.'
    ),
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def get_table(
    cafe_id: int,
    table_id: int,
    current_active_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Получение информации о столе с учётом прав пользователя."""
    await get_cafe_or_404(cafe_id, session)

    can_see_all = (
        current_active_user.role == UserRole.ADMIN
        or can_manage_cafe(current_active_user, cafe_id)
    )

    if not can_see_all:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Нет доступа к неактивному кафе',
        )

    table = await table_crud.get_by_cafe_and_id(
        session=session,
        cafe_id=cafe_id,
        table_id=table_id,
        show_all=can_see_all,
    )

    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Стол {table_id} не найден.',
        )

    return table


@router.patch(
    '/{table_id}',
    response_model=TableInfo,
    dependencies=[Depends(current_admin_or_manager)],
    summary='Обновление информации о столе в кафе по его ID.',
    description='Обновляет только переданные поля. Для ADMIN и MANAGER.',
    responses={
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def update_table(
    cafe_id: int,
    table_id: int,
    update_data: TableUpdate,
    current_user: User = Depends(current_admin_or_manager),
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Обновление информации о столе (для администраторов и менеджеров)."""
    await get_cafe_or_404(cafe_id, session)

    if (
        not can_manage_cafe(current_user, cafe_id)
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='У вас нет прав управлять столами этого кафе.',
        )

    table = await table_crud.get_by_cafe_and_id(
        session=session,
        cafe_id=cafe_id,
        table_id=table_id,
        show_all=True,
    )

    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Стол {table_id} не найден.',
        )

    return await table_crud.update(
        db_obj=table,
        obj_in=update_data,
        session=session,
    )


@router.post(
    '',
    response_model=TableInfo,
    dependencies=[Depends(current_admin_or_manager)],
    summary='Создаёт новый стол в кафе с указанными параметрами.',
    description='Доступно только для ADMIN и MANAGER.',
    responses={
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def create_table(
    cafe_id: int,
    data: TableCreate,
    current_user: User = Depends(current_admin_or_manager),
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Новый стол в кафе (для администраторов и менеджеров)."""
    await get_cafe_or_404(cafe_id, session)

    if (
        not can_manage_cafe(current_user, cafe_id)
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Нельзя создавать столы в чужом кафе.',
        )

    create_data = data.model_dump()
    create_data['cafe_id'] = cafe_id

    return await table_crud.create(
        obj_in=create_data,
        session=session,
    )


@router.get(
    '',
    response_model=list[TableInfo],
    summary='Получение списка доступных для бронирования столов в кафе.',
    description='Для администраторов и менеджеров - все столы, '
                'для пользователей - только активные.',
    responses={
        **NOT_FOUND_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def list_tables(
    cafe_id: int,
    show_all: bool = Query(default=False),
    current_active_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[Table]:
    """Список столов с учётом прав пользователя и выбором полного списка."""
    cafe = await get_cafe_or_404(cafe_id, session)

    can_see_all = (
        current_active_user.role == UserRole.ADMIN
        or can_manage_cafe(current_active_user, cafe_id)
    )

    if not cafe.is_active and not can_see_all:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Нет доступа к неактивному кафе',
        )

    filters = [{'field': 'cafe_id', 'op': 'eq', 'value': cafe_id}]

    if not can_see_all or not show_all:
        filters.append({'field': 'is_active', 'op': 'eq', 'value': True})

    return await table_crud.get_multi(
        filters=filters,
        session=session,
        options=[selectinload(Table.cafe)],
    )


@router.delete(
    '/{table_id}',
    response_model=TableInfo,
    dependencies=[Depends(current_admin_or_manager)],
    summary='Мягкое удаление стола (деактивация), для ADMIN и MANAGER.',
    description='Деактивирует стол, устанавливая is_active=False.',
    responses={
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def delete_table(
    cafe_id: int,
    table_id: int,
    current_user: User = Depends(current_admin_or_manager),
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Мягкое удаление стола (для администраторов и менеджеров)."""
    await get_cafe_or_404(cafe_id, session)

    if (
        not can_manage_cafe(current_user, cafe_id)
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Нельзя удалять столы в чужом кафе.',
        )

    table = await table_crud.get_by_cafe_and_id(
        session=session,
        cafe_id=cafe_id,
        table_id=table_id,
        show_all=True,
    )

    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Стол {table_id} не найден.',
        )

    table.is_active = False
    session.add(table)
    await session.commit()
    await session.refresh(table, attribute_names=['cafe'])

    return table
