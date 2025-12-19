from datetime import date
from typing import List, Optional, Any, Type

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.crud_base import BaseCRUD
from app.models.bookings import Booking, TableSlot
from app.models.enum import BookingStatus
from app.schemas.bookings import BookingCreate, BookingUpdate


class BookingCRUD(BaseCRUD):
    """CRUD для бронирований, с учётом TableSlot и валидаций."""

    def __init__(self, model: Type[Booking] = Booking):
        super().__init__(model)

    async def get_bookings(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        cafe_id: Optional[int] = None,
        date_filter: Optional[date] = None,
    ) -> List[Booking]:
        """Получить список бронирований с фильтрацией."""
        query = select(self.model)
        if user_id is not None:
            query = query.where(self.model.user_id == user_id)
        if cafe_id is not None:
            query = query.where(self.model.cafe_id == cafe_id)
        if date_filter is not None:
            query = query.where(self.model.date == date_filter)

        result = await session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def create_booking(
        self,
        session: AsyncSession,
        booking_in: BookingCreate,
        user_id: int,
    ) -> Booking:
        """Создать бронирование с проверкой даты и TableSlot."""
        if booking_in.booking_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя создать бронирование на прошедшую дату",
            )

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

        for ts in booking_in.tables_slots:
            table_slot = await session.get(
                TableSlot,
                {
                    "table_id": ts.table_id,
                    "slot_id": ts.slot_id,
                },
            )
            if not table_slot:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Указанный слот не существует",
                )
            table_slot.booking_id = booking.id

        await session.commit()
        await session.refresh(booking)
        return booking

    async def update_booking(
        self,
        session: AsyncSession,
        booking_id: int,
        updates: BookingUpdate,
    ) -> Optional[Booking]:
        """Обновить бронирование по ID."""
        booking = await self.get_by_id(booking_id, session)
        if not booking:
            return None

        data: dict[str, Any] = {}
        if updates.status is not None:
            data["status"] = updates.status
        if updates.note is not None:
            data["note"] = updates.note

        if data:
            booking = await self.update(booking, data, session)
        return booking

    async def delete_booking(
        self, session: AsyncSession, booking_id: int,
    ) -> bool:
        """Удаление бронирования."""
        booking = await self.get_by_id(booking_id, session)
        if not booking:
            return False
        await session.delete(booking)
        await session.commit()
        return True


booking_crud = BookingCRUD()
