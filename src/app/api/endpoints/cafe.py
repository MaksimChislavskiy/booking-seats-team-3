from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.crud.cafe import cafe_crud
from app.schemas.cafe import CafeCreate, CafeInfo, CafeUpdate

router = APIRouter()


@router.post(
    '/',
    response_model=CafeInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового кафе',
    description='Создаёт новое кафе с указанными параметрами.',
)
async def create(
    cafe_in: CafeCreate,
    session: AsyncSession = Depends(get_async_session),
) -> CafeInfo:
    """Создаёт новое кафе."""
    return await cafe_crud.create(session, cafe_in)


@router.get(
    '/',
    response_model=list[CafeInfo],
    summary='Получение списка кафе',
)
async def read_list(
    session: AsyncSession = Depends(get_async_session),
) -> list[CafeInfo]:
    """Получение списка кафе.

    Для администраторов и менеджеров - все кафе (с возможностью выбора),
    для пользователей - только активные.
    """
    return await cafe_crud.get_multi(session)


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Получение информации о кафе по его ID',
)
async def read(
    cafe_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> CafeInfo:
    """Получение информации о кафе по его ID.

    Для администраторов и менеджеров - все кафе,
    для пользователей - только активные.
    """
    cafe = await cafe_crud.get(session, cafe_id)
    if not cafe:
        raise HTTPException(status_code=404, detail='Кафе не найдено')
    return cafe


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Обновление информации о кафе по его ID',
)
async def update(
    cafe_id: int,
    cafe_in: CafeUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> CafeInfo:
    """Обновление информации о кафе по его ID.

    Только для администраторов и менеджеров.
    """
    cafe = await cafe_crud.get(session, cafe_id)
    if not cafe:
        raise HTTPException(status_code=404, detail='Кафе не найдено')
    return await cafe_crud.update(session, cafe, cafe_in)


@router.delete(
    '/{cafe_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удаление кафе',
    description='Удаляет кафе и связанные данные (cascade).',
)
async def delete(
    cafe_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Удаляет кафе."""
    cafe = await cafe_crud.get(session, cafe_id)
    if not cafe:
        raise HTTPException(status_code=404, detail='Кафе не найдено')
    await cafe_crud.delete(session, cafe)
