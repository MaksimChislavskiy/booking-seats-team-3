from datetime import date

from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Booking, BookingStatus, TableSlotBooking
from app.schemas import BookingCreate, BookingUpdate


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD для работы с бронированиями.

    Использует базовые методы CRUDBase.
    Содержит только дополнительные методы выборки.
    """

    async def find_conflicting_bookings(
        self,
        cafe_id: int,
        booking_date: date,
        table_ids: set[int],
        slot_ids: set[int],
        *,
        exclude_booking_id: int | None = None,
        session: AsyncSession,
    ) -> list[Booking]:
        # FIXME: docstring
        stmt = (
            select(Booking)
            .distinct()
            .join(
                TableSlotBooking,
                TableSlotBooking.booking_id == Booking.id,
            )
        ).where(
            Booking.cafe_id == cafe_id,
            Booking.booking_date == booking_date,
            Booking.status.in_(
                [BookingStatus.PENDING, BookingStatus.CONFIRMED],
            ),
            TableSlotBooking.table_id.in_(table_ids),
            TableSlotBooking.slot_id.in_(slot_ids),
        )

        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)

        result = await session.execute(stmt)
        return result.scalars().all()

    # FIXME: Удалить ненужные методы
    async def get_by_user(
        self,
        user_id: int,
        session: AsyncSession,
    ) -> list[Booking]:
        """Возвращает все бронирования пользователя."""
        stmt = select(Booking).where(Booking.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_cafe(
        self,
        cafe_id: int,
        session: AsyncSession,
    ) -> list[Booking]:
        """Возвращает все бронирования кафе."""
        stmt = select(Booking).where(Booking.cafe_id == cafe_id)
        result = await session.execute(stmt)
        return result.scalars().all()


booking_crud = CRUDBooking(Booking)
