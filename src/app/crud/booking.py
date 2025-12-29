# === Твой код ===
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models import Booking, BookingStatus, TableSlot
from app.schemas.booking import BookingCreate, BookingUpdate, TableSlotCreate


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD для бронирований, с учётом TableSlot и валидаций."""

    async def get_bookings(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        user_id: int | None = None,
        cafe_id: int | None = None,
    ) -> list[Booking]:
        """Получить список бронирований с фильтрацией."""
        query = select(self.model)
        if user_id is not None:
            query = query.where(self.model.user_id == user_id)
        if cafe_id is not None:
            query = query.where(self.model.cafe_id == cafe_id)
        result = await session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def create_booking(
        self,
        session: AsyncSession,
        booking_in: BookingCreate,
        user_id: int,
    ) -> Booking:
        """Создать бронирование и привязать к нему свободные слоты."""
        booking = self.model(
            user_id=user_id,
            cafe_id=booking_in.cafe_id,
            guest_number=booking_in.guest_number,
            note=booking_in.note,
            date=booking_in.booking_date,
            status=BookingStatus.pending,
        )

        session.add(booking)
        await session.flush()

        await self._attach_table_slots(
            session=session,
            booking_id=booking.id,
            tables_slots=booking_in.tables_slots,
        )
        await session.commit()
        await session.refresh(booking)
        return booking

    async def _attach_table_slots(
        self,
        session: AsyncSession,
        booking_id: int,
        tables_slots: list[TableSlotCreate],
    ) -> None:
        """Привязать свободные столы и слоты к бронированию."""
        for ts in tables_slots:
            stmt = select(TableSlot).where(
                TableSlot.table_id == ts.table_id,
                TableSlot.slot_id == ts.slot_id,
                TableSlot.booking_id.is_(None),
            )
            result = await session.execute(stmt)
            table_slot = result.scalar_one_or_none()

            if not table_slot:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Указанный стол или слот недоступен',
                )

            table_slot.booking_id = booking_id

    async def update_booking(
        self,
        session: AsyncSession,
        booking_id: int,
        updates: BookingUpdate,
    ) -> Booking | None:
        """Обновить бронирование по ID."""
        booking = await self.get_by_id(booking_id, session)
        if not booking:
            return None

        booking = await self.update(
            booking,
            updates,
            session=session,
        )
        return await self.update(
            booking,
            updates,
            session=session,
        )

    async def deactivate_booking(
        self,
        session: AsyncSession,
        booking_id: int,
        user_id: int,
        is_admin: bool,
    ) -> Booking:
        """Деактивировать бронирование."""
        booking = await session.get(Booking, booking_id)

        if not booking or not booking.active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Бронирование не найдено',
            )

        if not is_admin and booking.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Недостаточно прав для удаления бронирования',
            )

        await self.soft_delete(booking, session)
        await session.refresh(booking)
        return booking


# === Текущий код из ветки develop ===
# booking_crud = CRUDBooking()
# from app.crud.base import CRUDBase
# from app.models import Booking
# from app.schemas import BookingCreate, BookingUpdate


# class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
#     """CRUD для модели Booking."""

#     pass


# booking_crud = CRUDBooking(Booking)
