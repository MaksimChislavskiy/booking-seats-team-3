from datetime import time

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Slot
from app.schemas import TimeSlotCreate, TimeSlotUpdate


class CRUDSlot(CRUDBase):
    """CRUD-операции для временных слотов."""

    async def get_cafe_slots(
        self,
        cafe_id: int,
        show_all: bool = False,
        *,
        session: AsyncSession,
    ) -> list[Slot]:  # FIXME: Update docstring
        """Получает список временных слотов в кафе.

        Args:
            cafe_id: ID кафе
            show_all: Показывать все слоты или только активные
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Список временных слотов кафе

        """
        filters = [{'field': 'cafe_id', 'op': 'eq', 'value': cafe_id}]

        if not show_all:
            filters.append({'field': 'is_active', 'op': 'eq', 'value': True})

        return await self.get_multi(filters, session=session)

    async def get_by_id_and_cafe(  # FIXME: name?
        self,
        slot_id: int,
        cafe_id: int,
        session: AsyncSession,
    ) -> Slot | None:
        """Возвращает временной слот по ID и ID кафе.

        Args:
            slot_id: Идентификатор слота.
            cafe_id: Идентификатор кафе.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Слот или None, если не найден.

        """
        stmt = select(Slot).where(
            and_(
                Slot.id == slot_id,
                Slot.cafe_id == cafe_id,
            ),
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    # async def create_with_cafe(  # FIXME: Удалить это
    #     self,
    #     session: AsyncSession,
    #     slot_in: TimeSlotCreate,
    # ) -> Slot:
    #     """Создает новый временной слот.

    #     Args:
    #         session: Асинхронная сессия БД
    #         slot_in: Данные для создания слота

    #     Returns:
    #         Созданный слот

    #     """
    #     db_slot = Slot(
    #         cafe_id=slot_in.cafe_id,
    #         start_time=slot_in.start_time,
    #         end_time=slot_in.end_time,
    #         description=slot_in.description,
    #     )

    #     return await self.create(db_slot, session)

    async def update_slot(  # FIXME: Удалить это?
        self,
        session: AsyncSession,
        db_slot: Slot,
        slot_in: TimeSlotUpdate,
    ) -> Slot:
        """Обновляет существующий временной слот.

        Args:
            session: Асинхронная SQLAlchemy-сессия.
            db_slot: Существующий слот из БД
            slot_in: Данные для обновления

        Returns:
            Обновленный слот

        """
        update_data = slot_in.model_dump(exclude_unset=True)
        return await self.update(db_slot, update_data, session)

    # FIXME: Удалить это
    # async def check_time_slot_exists(
    #     self,
    #     cafe_id: int,
    #     start_time: time,
    #     end_time: time,
    #     exclude_slot_id: int | None = None,
    #     *,
    #     session: AsyncSession,
    # ) -> bool:
    #     """Проверяет существование слота с таким же интервалом в кафе.

    #     Args:
    #         session: Асинхронная сессия БД
    #         cafe_id: ID кафе
    #         start_time: Время начала (datetime.time)
    #         end_time: Время окончания (datetime.time)
    #         exclude_slot_id: ID слота для исключения (при обновлении)

    #     Returns:
    #         True если слот существует, иначе False

    #     """
    #     stmt = select(Slot).where(
    #         and_(
    #             Slot.cafe_id == cafe_id,
    #             Slot.start_time == start_time,
    #             Slot.end_time == end_time,
    #         ),
    #     )

    #     if exclude_slot_id is not None:
    #         stmt = stmt.where(Slot.id != exclude_slot_id)

    #     result = await session.execute(stmt)
    #     slot = result.scalar_one_or_none()
    #     return slot is not None

    async def get_slot_by_time_range(
        self,
        cafe_id: int,
        start_time: time,
        end_time: time,
        *,
        session: AsyncSession,
    ) -> Slot | None:
        """Возвращает слот с точным временным интервалом в кафе.

        Используется для проверки уникальности слота.

        Args:
            cafe_id: Идентификатор кафе.
            start_time: Время начала слота.
            end_time: Время окончания слота.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Слот, если найден, иначе None.

        """
        stmt = select(Slot).where(
            and_(
                Slot.cafe_id == cafe_id,
                Slot.start_time == start_time,
                Slot.end_time == end_time,
            ),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_overlapping_slots(
        self,
        cafe_id: int,
        start_time: time,
        end_time: time,
        *,
        session: AsyncSession,
    ) -> list[Slot]:
        # FIXME: docstring
        """Возвращает активные слоты, пересекающиеся с временным диапазоном.

        Используется для проверки конфликтов при создании и обновлении слотов.
        Неактивные слоты не должны блокировать управление расписанием.

        Args:
            cafe_id: Идентификатор кафе.
            start_time: Время начала диапазона.
            end_time: Время окончания диапазона.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Список активных слотов, пересекающихся с диапазоном.

        """
        # FIXME: правильная ли проверка? Как она работает получше узнать
        stmt = select(Slot).where(
            and_(
                Slot.cafe_id == cafe_id,
                Slot.is_active.is_(True),
                Slot.start_time < end_time,
                Slot.end_time > start_time,
            ),
        )

        result = await session.execute(stmt)
        return result.scalars().all()


slot_crud = CRUDSlot(Slot)
