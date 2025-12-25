from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from app.core.user import current_manager_or_admin, current_user
from crud.table import table_crud
from models import Table, User, UserRole
from schemas.table import TableCreate, TableInfo, TableUpdate
from validators.table import check_cafe_exists

router = APIRouter()


@router.get(
    '/{table_id}',
    response_model=TableInfo,
    summary='Получение информации о столе в кафе по его ID.',
    description='Для администраторов и менеджеров - все столы, '
                'для пользователей - только активные.',
)
async def get_table(
    cafe_id: int,
    table_id: int,
    current_user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Получение информации о столе с учётом прав пользователя."""
    cafe = await check_cafe_exists(cafe_id, session)
    table = await table_crud.get_by_id_id_active(
        session=session,
        cafe_id=cafe.id,
        id=table_id,
        user_role=current_user.role
    )
    if not table:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Стол {table_id} не найден.',
        )
    return table


@router.patch(
    "/{table_id}",
    response_model=TableInfo,
    dependencies=[Depends(current_manager_or_admin)],
    summary='Обновление информации о столе в кафе по его ID.',
    description='Обновляет только переданные поля. Для ADMIN и MANAGER.',
)
async def update_table(
    cafe_id: int,
    table_id: int,
    update_data: TableUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Обновление информации о столе (для администраторов и менеджеров)."""
    cafe = await check_cafe_exists(cafe_id, session)
    table = await table_crud.get_by_id_id(
        session=session,
        cafe_id=cafe.id,
        id=table_id,
    )
    if not table:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Стол {table_id} не найден.',
        )
    try:
        updated_table = await table_crud.update(
            db_obj=table,
            obj_in=update_data,
            session=session,
        )
    except Exception as e:
        logger.error(f'Failed to update table: {e}')
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Ошибка обновления"
        )
    return updated_table


@router.post(
    "/",
    response_model=TableInfo,
    dependencies=[Depends(current_manager_or_admin)],
    summary='Создаёт новый стол в кафе с указанными параметрами.',
    description='Доступно только для ADMIN и MANAGER.',
)
async def create_table(
    cafe_id: int,
    data: TableCreate,
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Новый стол в кафе (для администраторов и менеджеров)."""
    await check_cafe_exists(cafe_id, session)
    new_table = await table_crud.create(
        obj_in=data,
        session=session,
        )
    return new_table


@router.get(
    "/",
    response_model=list[TableInfo],
    summary='Получение списка доступных для бронирования столов в кафе.',
    description='Для администраторов и менеджеров - все столы, '
                'для пользователей - только активные.',
)
async def list_tables(
    cafe_id: int,
    show_all: bool = Query(default=False),
    current_user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[Table]:
    """Список столов с учётом прав пользователя и выбором полного списка."""
    await check_cafe_exists(cafe_id, session)
    can_show_all = current_user.role in {UserRole.ADMIN, UserRole.MANAGER}
    if show_all and can_show_all:
        filters = [
            {"field": "cafe_id", "op": "eq", "value": cafe_id},
        ]
    if not show_all or not can_show_all:
        filters.append({"field": "is_active", "op": "eq", "value": True})
    tables = await table_crud.get_multi(filters=filters, session=session)
    return tables
