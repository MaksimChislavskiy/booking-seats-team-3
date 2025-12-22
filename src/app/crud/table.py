from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Table, UserRole


class CRUDTable(CRUDBase):
    """CRUD для столов."""

    async def get_by_id_with_permissions(
        self,
        session: AsyncSession,
        cafe_id: int,
        id: int,
        user_role: UserRole
    ) -> Table | None:
        """
        Получение стола по ID с учётом прав пользователя:

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


table_crud = CRUDTable(Table)
