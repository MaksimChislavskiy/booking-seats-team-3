from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class CafeCRUD:
    """Заглушка для cafe_crud до реализации."""

    async def get(self, db: AsyncSession, cafe_id: int) -> Any | None:
        """Получить кафе по ID.

        Временная заглушка, всегда возвращает None.

        Args:
            db: Асинхронная сессия базы данных
            cafe_id: Идентификатор кафе

        Returns:
            Any | None: Всегда возвращает None

        """
        return None


cafe_crud = CafeCRUD()
