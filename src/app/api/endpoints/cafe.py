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
    summary='Список кафе',
    description='Возвращает список всех кафе.',
)
async def read_list(
    session: AsyncSession = Depends(get_async_session),
) -> list[CafeInfo]:
    """Возвращает список всех кафе."""
    return await cafe_crud.get_multi(session)


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Получение кафе по ID',
    description='Возвращает информацию о конкретном кафе.',
)
async def read(
    cafe_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> CafeInfo:
    """Возвращает информацию о кафе."""
    cafe = await cafe_crud.get(session, cafe_id)
    if not cafe:
        raise HTTPException(status_code=404, detail='Кафе не найдено')
    return cafe


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Обновление кафе',
    description='Частичное обновление данных кафе.',
)
async def update(
    cafe_id: int,
    cafe_in: CafeUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> CafeInfo:
    """Обновляет данные кафе."""
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
