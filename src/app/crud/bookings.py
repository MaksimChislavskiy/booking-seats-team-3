from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.bookings import Booking, TableSlot
from app.models.enum import BookingStatus
from app.schemas.bookings import BookingCreate, BookingUpdate


async def get_booking(db: AsyncSession, booking_id: int) -> Optional[Booking]:
    """Получить бронирование по ID."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    return result.scalar_one_or_none()


async def get_bookings(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    cafe_id: Optional[int] = None,
    date_filter: Optional[date] = None,
) -> List[Booking]:
    """Получить список бронирований с возможностью фильтрации."""
    query = select(Booking)
    if user_id:
        query = query.where(Booking.user_id == user_id)
    if cafe_id:
        query = query.where(Booking.cafe_id == cafe_id)
    if date_filter:
        query = query.where(Booking.date == date_filter)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


async def create_booking(
    db: AsyncSession,
    booking_in: BookingCreate,
    user_id: int,
) -> Booking:
    """Создать бронирование."""

    if booking_in.booking_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя создать бронирование на прошедшую дату",
        )

    booking = Booking(
        user_id=user_id,
        cafe_id=booking_in.cafe_id,
        guest_number=booking_in.guest_number,
        note=booking_in.note,
        date=booking_in.booking_date,
        status=BookingStatus.pending,
    )
    db.add(booking)
    await db.flush()

    for ts in booking_in.tables_slots:
        table_slot = await db.get(
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

    await db.commit()
    await db.refresh(booking)
    return booking



async def update_booking(
    db: AsyncSession,
    booking_id: int,
    updates: BookingUpdate,
) -> Optional[Booking]:
    """Изменить существующее бронирование."""
    db_booking = await get_booking(db, booking_id)
    if not db_booking:
        return None

    if updates.status is not None:
        db_booking.status = updates.status
    if updates.note is not None:
        db_booking.note = updates.note

    await db.commit()
    await db.refresh(db_booking)
    return db_booking


async def delete_booking(db: AsyncSession, booking_id: int) -> bool:
    """Удалить бронирование по ID."""
    db_booking = await get_booking(db, booking_id)
    if not db_booking:
        return False
    await db.delete(db_booking)
    await db.commit()
    return True
