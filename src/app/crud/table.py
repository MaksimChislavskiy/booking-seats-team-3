from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Table, UserRole


class CRUDTable(CRUDBase):
    """CRUD для столов."""

    async def get_by_id_id(
        self,
        session: AsyncSession,
        cafe_id: int,
        id: int,
        user_role: UserRole
    ) -> Table | None:
        """Получение стола по ID с учётом прав пользователя:

        - Для USER: только активные столы (is_active=True)
        - Для ADMIN/MANAGER: любые столы
        """
        query = select(Table).where(
            Table.cafe_id == cafe_id,
            Table.id == id
        )

        if user_role == UserRole.USER:
            query = query.where(Table.is_active)

        result = await session.execute(query)
        return result.scalars().first()

    async def update_by_id_id(
        self,
        session: AsyncSession,
        cafe_id: int,
        table_id: int,
        update_data: dict,
    ) -> Table | None:
        """Обновление стола по ID.
        Вызывающий имеет достаточные права (ADMIN/MANAGER).
        """
        query = select(Table).where(
            Table.cafe_id == cafe_id,
            Table.id == table_id
        )
        result = await session.execute(query)
        table = result.scalars().first()

        if not table:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f'Стол {table_id} не найден.',
            )

        for key, value in update_data.items():
            if hasattr(table, key):
                setattr(table, key, value)

        await session.commit()
        await session.refresh(table)
        return table


table_crud = CRUDTable(Table)
