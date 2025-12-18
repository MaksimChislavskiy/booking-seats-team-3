# TODO: Задачу доделывает @Khoetskiy

from typing import Any, Optional, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseCRUD:
    """Базовый CRUD-класс.

    Содержит стандартные операции Create, Read, Update, Delete,
    применимые ко всем сущностям проекта.
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

    async def get_multi(
        self,
        session: AsyncSession,
    ) -> list[Any]:
        """Получает список активных объектов."""
        result = await session.execute(
            select(self.model).where(self.model.active.is_(True)),
        )
        return result.scalars().all()

    async def create(
        self,
        obj: Any,
        session: AsyncSession,
    ) -> Any:
        """Создает объект."""
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(
        self,
        obj: Any,
        data: dict[str, Any],
        session: AsyncSession,
    ) -> Any:
        """Обновляет объект."""
        for field, value in data.items():
            setattr(obj, field, value)

        await session.commit()
        await session.refresh(obj)
        return obj

    async def soft_delete(
        self,
        obj: Any,
        session: AsyncSession,
    ) -> Any:
        """Мягкое удаление объекта (active = False)."""
        obj.active = False
        await session.commit()
        return obj
