from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Cafe
from app.schemas import CafeCreate, CafeUpdate


class CRUDCafe(CRUDBase[Cafe, CafeCreate, CafeUpdate]):
    # FIXME: docstring
    """CRUD-операции для модели Cafe."""

    async def get_cafes(
        self,
        show_all: bool = False,
        *,
        session: AsyncSession,
    ) -> list[Cafe]:
        """Возвращает список кафе с учётом флага отображения неактивных.

        По умолчанию возвращаются только активные кафе.
        Если `show_all=True`, возвращаются все кафе без фильтрации.

        Args:
            show_all: Если True — вернуть все кафе,
                если False — только активные.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Список объектов Cafe.

        """
        if show_all:
            return await self.get_multi(session=session)

        return await self.get_active_cafes(session=session)

    async def get_active_cafes(self, session: AsyncSession) -> list[Cafe]:
        """Возвращает только активные кафе.

        Args:
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Список объектов Cafe с `is_active=True`.

        """
        return await self.get_multi(
            filters=[
                {
                    'field': 'is_active',
                    'op': 'eq',
                    'value': True,
                },
            ],
            session=session,
        )

    async def get_active_and_own_cafes(
        self,
        cafe_id: int | None,
        session: AsyncSession,
    ) -> list[Cafe]:
        """Возвращает активные кафе и кафе, управляемое менеджером.

        Используется для менеджеров:
        - всегда возвращает все активные кафе;
        - дополнительно возвращает кафе, в котором пользователь
                    является менеджером, даже если оно неактивно.

        Args:
            cafe_id: Идентификатор кафе, которым управляет менеджер.
                Если None — возвращаются только активные кафе.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Список объектов Cafe.

        """
        if cafe_id is None:
            return await self.get_active_cafes(session)

        return await self.get_multi(
            filters=[
                {
                    'logic': 'or',
                    'conditions': [
                        {'field': 'is_active', 'op': 'eq', 'value': True},
                        {'field': 'id', 'op': 'eq', 'value': cafe_id},
                    ],
                },
            ],
            session=session,
        )

    async def get_by_name_and_address(
        self,
        name: str,
        address: str,
        *,
        session: AsyncSession,
    ) -> Cafe | None:
        """Возвращает кафе с указанным названием и адресом, если существует.

        Args:
            name: Название кафе.
            address: Адрес кафе.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Объект Cafe, если кафе найдено, иначе None.

        """
        stmt = select(Cafe).where(
            Cafe.name == name,
            Cafe.address == address,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


cafe_crud = CRUDCafe(Cafe)
