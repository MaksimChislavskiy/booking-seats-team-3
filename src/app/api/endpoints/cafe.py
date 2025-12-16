from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.db import get_async_session
from app.crud.cafe import (
    create_cafe,
    delete_cafe,
    get_cafe_by_id,
    get_cafes_list,
    update_cafe,
)
from app.schemas.cafe import CafeCreate, CafeRead, CafeUpdate

router = APIRouter(tags=["Кафе"])


@router.post("/", response_model=CafeRead, status_code=status.HTTP_201_CREATED)
async def create_cafe_endpoint(
    cafe_in: CafeCreate,
    db: AsyncSession = Depends(get_async_session),
) -> CafeRead:
    """Создание нового кафе."""
    return await create_cafe(db, cafe_in)


@router.get("/", response_model=List[CafeRead])
async def get_cafes_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
) -> List[CafeRead]:
    """Список всех кафе с пагинацией."""
    return await get_cafes_list(db, skip=skip, limit=limit)


@router.get("/{cafe_id}", response_model=CafeRead)
async def get_cafe_endpoint(
    cafe_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> CafeRead:
    """Получение кафе по ID."""
    cafe = await get_cafe_by_id(db, cafe_id)
    if not cafe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кафе не найдено",
        )
    return cafe


@router.patch("/{cafe_id}", response_model=CafeRead)
async def update_cafe_endpoint(
    cafe_id: int,
    cafe_in: CafeUpdate,
    db: AsyncSession = Depends(get_async_session),
) -> CafeRead:
    """Обновление кафе."""
    cafe = await get_cafe_by_id(db, cafe_id)
    if not cafe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кафе не найдено",
        )
    return await update_cafe(db, cafe, cafe_in)


@router.delete("/{cafe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cafe_endpoint(
    cafe_id: int,
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Удаление кафе."""
    cafe = await get_cafe_by_id(db, cafe_id)
    if not cafe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кафе не найдено",
        )
    await delete_cafe(db, cafe)
