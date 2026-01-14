import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models import Table
from app.schemas import TableCreate, TableUpdate

logger = logging.getLogger(__name__)


class CRUDTable(CRUDBase[Table, TableCreate, TableUpdate]):
    """CRUD для столов."""

    async def get_by_cafe_and_id(
        self,
        session: AsyncSession,
        cafe_id: int,
        table_id: int,
        show_all: bool = False,
    ) -> Table | None:
        """Получение стола по ID для данного кафе с учётом show_all."""
        logger.info(
            'Запрос стола. cafe_id=%d, table_id=%d, show_all=%s',
            cafe_id,
            table_id,
            show_all,
        )

        query = select(Table).where(
            Table.cafe_id == cafe_id,
            Table.id == table_id,
        )

        if not show_all:
            query = query.where(Table.is_active)

        query = query.options(selectinload(Table.cafe))
        result = await session.execute(query)
        return result.scalars().first()


table_crud = CRUDTable(Table)
