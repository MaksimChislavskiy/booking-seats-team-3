from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.cafes import Cafe
from app.schemas.cafe import CafeCreate, CafeUpdate


async def create_cafe(db: AsyncSession, cafe_in: CafeCreate) -> Cafe:
    """Создаёт новое кафе."""
    cafe = Cafe(**cafe_in.model_dump())
    db.add(cafe)
    await db.commit()
    await db.refresh(cafe)
    return cafe


async def get_cafe_by_id(db: AsyncSession, cafe_id: int) -> Optional[Cafe]:
    """Возвращает кафе по ID."""
    result = await db.execute(
        select(Cafe).where(Cafe.id == cafe_id),
    )
    return result.scalar_one_or_none()


async def get_cafes_list(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> List[Cafe]:
    """Возвращает список кафе с пагинацией."""
    result = await db.execute(
        select(Cafe).offset(skip).limit(limit),
    )
    return result.scalars().all()


async def update_cafe(
    db: AsyncSession,
    cafe: Cafe,
    cafe_in: CafeUpdate,
) -> Cafe:
    """Обновляет кафе."""
    update_data = cafe_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cafe, field, value)
    await db.commit()
    await db.refresh(cafe)
    return cafe


async def delete_cafe(db: AsyncSession, cafe: Cafe) -> None:
    """Удаляет кафе (можно заменить на soft-delete)."""
    await db.delete(cafe)
    await db.commit()
