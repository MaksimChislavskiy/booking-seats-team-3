from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import setup_logging
from app.crud.base import CRUDBase
from app.models import Table, UserRole

logger = setup_logging()


class CRUDTable(CRUDBase):
    """CRUD для столов."""

    async def get_by_id_id(
        self,
        session: AsyncSession,
        cafe_id: int,
        id: int,
    ) -> Table | None:
        """Получение стола по ID с учётом прав пользователя:

        - Для USER: только активные столы (is_active=True)
        - Для ADMIN/MANAGER: любые столы
        """
        logger.info(
            'Запрос стола. cafe_id=%d, table_id=%d',
            cafe_id, id,
            extra={'cafe_id': cafe_id, 'table_id': id},
        )
        result = await session.execute(
            select(Table).where(
                Table.cafe_id == cafe_id,
                Table.id == id,
            )
        )
        return result.scalars().first()

    async def get_by_id_id_active(
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
        logger.info(
            'Запрос стола с фильтрацией по роли. '
            'cafe_id=%d, table_id=%d, роль=%s',
            cafe_id, id, user_role.value,
            extra={
                'cafe_id': cafe_id,
                'table_id': id,
                'user_role': user_role.value},
        )
        query = select(Table).where(
            Table.cafe_id == cafe_id,
            Table.id == id,
        )
        if user_role == UserRole.USER:
            logger.debug(
                'Фильтрация по is_active для USER. cafe_id=%d, table_id=%d',
                cafe_id, id,
                extra={
                    'cafe_id': cafe_id,
                    'table_id': id,
                    'user_role': user_role.value},
            )
            query = query.where(Table.is_active)
        else:
            logger.debug(
                'Доступ без фильтрации. cafe_id=%d, table_id=%d, роль=%s',
                cafe_id, id, user_role.value,
                extra={
                    'cafe_id': cafe_id,
                    'table_id': id,
                    'user_role': user_role.value},
            )
        result = await session.execute(query)
        return result.scalars().first()


table_crud = CRUDTable(Table)
