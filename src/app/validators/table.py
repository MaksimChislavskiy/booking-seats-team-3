from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from crud.cafe import cafe_crud
from models.cafe import Cafe


async def check_cafe_exists(
        cafe_id: int,
        session: AsyncSession,
) -> Cafe:
    """Проверяет существование кафе."""
    cafe = await cafe_crud.get_by_id(
        cafe_id, session
    )
    if cafe is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Кафе {cafe_id} не найдено.'
        )
    return cafe
