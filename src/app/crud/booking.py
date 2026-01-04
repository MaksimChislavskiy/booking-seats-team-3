from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Booking
from app.schemas import BookingCreate, BookingUpdate


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD для работы с бронированиями.

    Использует базовые методы CRUDBase.
    Содержит только дополнительные методы выборки.
    """

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
