from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.db import get_async_session
from src.app.crud.cafe import (
    create_cafe,
    delete_cafe,
    get_cafe_by_id,
    get_cafes_list,
    update_cafe,
)
from src.app.schemas.cafe import CafeCreate, CafeRead, CafeUpdate

router = APIRouter()


async def get_cafe_or_404(
    cafe_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> CafeRead:
    """Получает кафе по ID или вызывает 404."""
    cafe = await get_cafe_by_id(db, cafe_id)
    if not cafe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Кафе не найдено',
        )
    return cafe


@router.post(
    '/',
    response_model=CafeRead,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового кафе',
    description='Создаёт новое кафе с указанными параметрами.',
)
async def create(
    cafe_in: CafeCreate,
    db: AsyncSession = Depends(get_async_session),
) -> CafeRead:
    """Создаёт новое кафе."""
    return await create_cafe(db, cafe_in)


@router.get(
    '/',
    response_model=list[CafeRead],
    summary='Список кафе',
    description='Возвращает список всех кафе с пагинацией.',
)
async def read_list(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
) -> list[CafeRead]:
    """Возвращает список всех кафе."""
    return await get_cafes_list(db, skip=skip, limit=limit)


@router.get(
    '/{cafe_id}',
    response_model=CafeRead,
    summary='Получение кафе по ID',
    description='Возвращает информацию о конкретном кафе.',
)
async def read(
    cafe: CafeRead = Depends(get_cafe_or_404),
) -> CafeRead:
    """Возвращает информацию о кафе."""
    return cafe


@router.patch(
    '/{cafe_id}',
    response_model=CafeRead,
    summary='Обновление кафе',
    description='Частичное обновление данных кафе.',
)
async def update(
    cafe_in: CafeUpdate,
    cafe: CafeRead = Depends(get_cafe_or_404),
) -> CafeRead:
    """Обновляет данные кафе."""
    return await update_cafe(db=cafe.session, cafe=cafe, cafe_in=cafe_in)


@router.delete(
    '/{cafe_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удаление кафе',
    description='Удаляет кафе и связанные данные (cascade).',
)
async def delete(
    cafe: CafeRead = Depends(get_cafe_or_404),
) -> None:
    """Удаляет кафе."""
    await delete_cafe(db=cafe.session, cafe=cafe)
