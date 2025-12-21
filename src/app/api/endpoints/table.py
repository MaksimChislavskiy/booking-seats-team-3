from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from app.core.user import current_user
from crud.table import table_crud
from models import Table
from schemas.table import TableInfo
from validators.table import check_cafe_exists

router = APIRouter()


@router.get(
    '/{table_id}',
    response_model=TableInfo,
    summary='Получение информации о столе в кафе по его ID.'
            'Для администраторов и менеджеров - все столы, '
            'для пользователей - только активные.',
)
async def get_table(
    cafe_id: int,
    table_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Получаем стол по ID с учётом прав пользователя."""
    cafe = await check_cafe_exists(cafe_id, session)
    table = await table_crud.get_by_id(
        session=session, cafe_id=cafe.id, id=table_id,
    )
    if not table:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Стол {table_id} не найден.',
        )
    return table
