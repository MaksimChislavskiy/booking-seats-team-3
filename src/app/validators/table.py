from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import setup_logging
from app.crud.cafe import cafe_crud
from app.models.cafe import Cafe

logger = setup_logging()


async def check_cafe_exists(
        cafe_id: int,
        session: AsyncSession,
) -> Cafe:
    """Проверяет существование кафе."""
    cafe = await cafe_crud.get_by_id(cafe_id, session)
    if cafe is None:
        logger.warning(
            'Кафе не найдено. ID=%d',
            cafe_id,
            extra={'cafe_id': cafe_id},
        )
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Кафе {cafe_id} не найдено.',
        )
    return cafe
