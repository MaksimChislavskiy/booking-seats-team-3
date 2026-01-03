from datetime import time as time_type

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Slot
from app.schemas import TimeSlotCreate, TimeSlotUpdate


class CRUDSlot(CRUDBase):
    """CRUD-операции для временных слотов."""

    async def get_cafe_slots(
        self,
        session: AsyncSession,
        cafe_id: int,
        show_all: bool = False,
    ) -> list[Slot]:
        """Получает временные слоты кафе.

        Args:
            session: Асинхронная сессия БД
            cafe_id: ID кафе
            show_all: Показывать все слоты или только активные

        Returns:
            Список временных слотов кафе

        """
        filters = [{"field": "cafe_id", "op": "eq", "value": cafe_id}]

        if not show_all:
            filters.append({"field": "is_active", "op": "eq", "value": True})

        return await self.get_multi(filters, session=session)

    async def get_by_id_and_cafe(
        self,
        session: AsyncSession,
        slot_id: int,
        cafe_id: int,
    ) -> Slot | None:
        """Получает слот по ID и ID кафе.

        Args:
            session: Асинхронная сессия БД
            slot_id: ID слота
            cafe_id: ID кафе

        Returns:
            Слот или None, если не найден

        """
        query = select(Slot).where(
            and_(
                Slot.id == slot_id,
                Slot.cafe_id == cafe_id,
            ),
        )

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create_with_cafe(
        self,
        session: AsyncSession,
        slot_in: TimeSlotCreate,
    ) -> Slot:
        """Создает новый временной слот.

        Args:
            session: Асинхронная сессия БД
            slot_in: Данные для создания слота

        Returns:
            Созданный слот

        """
        db_slot = Slot(
            cafe_id=slot_in.cafe_id,
            start_time=slot_in.start_time,
            end_time=slot_in.end_time,
            description=slot_in.description,
        )

        return await self.create(db_slot, session)

    async def update_slot(
        self,
        session: AsyncSession,
        db_slot: Slot,
        slot_in: TimeSlotUpdate,
    ) -> Slot:
        """Обновляет существующий временной слот.

        Args:
            session: Асинхронная сессия БД
            db_slot: Существующий слот из БД
            slot_in: Данные для обновления

        Returns:
            Обновленный слот

        """
        update_data = slot_in.model_dump(exclude_unset=True)
        return await self.update(db_slot, update_data, session)

    async def check_time_slot_exists(
        self,
        session: AsyncSession,
        cafe_id: int,
        start_time: time_type,
        end_time: time_type,
        exclude_slot_id: int | None = None,
    ) -> bool:
        """Проверяет существование слота с таким же интервалом в кафе.

        Args:
            session: Асинхронная сессия БД
            cafe_id: ID кафе
            start_time: Время начала (datetime.time)
            end_time: Время окончания (datetime.time)
            exclude_slot_id: ID слота для исключения (при обновлении)

        Returns:
            True если слот существует, иначе False

        """
        query = select(Slot).where(
            and_(
                Slot.cafe_id == cafe_id,
                Slot.start_time == start_time,
                Slot.end_time == end_time,
            ),
        )

        if exclude_slot_id is not None:
            query = query.where(Slot.id != exclude_slot_id)

        result = await session.execute(query)
        slot = result.scalar_one_or_none()
        return slot is not None

    async def get_slots_by_time_range(
        self,
        session: AsyncSession,
        cafe_id: int,
        start_time: time_type,
        end_time: time_type,
    ) -> list[Slot]:
        """Получает слоты, пересекающиеся с диапазоном времени.

        Args:
            session: Асинхронная сессия БД
            cafe_id: ID кафе
            start_time: Время начала диапазона (datetime.time)
            end_time: Время окончания диапазона (datetime.time)

        Returns:
            Список слотов, пересекающихся с диапазоном

        """
        query = select(Slot).where(
            and_(
                Slot.cafe_id == cafe_id,
                Slot.is_active.is_(True),
                Slot.start_time < end_time,
                Slot.end_time > start_time,
            ),
        )

        result = await session.execute(query)
        return list(result.scalars().all())


slot_crud = CRUDSlot(Slot)
