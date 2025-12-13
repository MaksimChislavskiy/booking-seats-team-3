from typing import Any, Optional, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseCRUD:
    """Минимальный базовый CRUD.

    Содержит общие операции, которые применимы
    ко всем сущностям проекта.
    """

    def __init__(self, model: Type) -> None:
        """Инициализирует CRUD с указанной SQLAlchemy-моделью."""
        self.model = model

    async def get_by_id(
        self,
        obj_id: int,
        session: AsyncSession,
    ) -> Optional[Any]:
        """Получает объект по его ID."""
        result = await session.execute(
            select(self.model).where(self.model.id == obj_id),
        )
        return result.scalar_one_or_none()

    async def soft_delete(
        self,
        obj: Any,
        session: AsyncSession,
    ) -> Any:
        """Мягкое удаление объекта (active = False)."""
        obj.active = False
        await session.commit()
        return obj
