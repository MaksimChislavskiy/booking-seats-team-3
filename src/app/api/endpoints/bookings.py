from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.security import get_current_user
from app.crud.bookings import get_bookings
from app.models.users import User
from app.schemas.bookings import BookingRead

router = APIRouter()


@router.get(
    "",
    response_model=List[BookingRead],
    status_code=status.HTTP_200_OK,
)
async def get_booking_list(
    show_all: bool = Query(
        default=False,
        description="Показывать все бронирования",
    ),
    cafe_id: Optional[int] = Query(
        default=None,
        description="ID кафе",
    ),
    user_id: Optional[int] = Query(
        default=None,
        description="ID пользователя",
    ),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> List[BookingRead]:
    """
    Получение списка бронирований.

    - Администраторы и менеджеры:
      - получают все бронирования
      - могут фильтровать по cafe_id
      - при show_all=true могут фильтровать по user_id

    - Пользователи:
      - получают только свои бронирования
      - user_id и show_all игнорируются
      - cafe_id учитывается
    """

    if not current_user.is_admin and not current_user.is_manager:
        return await get_bookings(
            db=db,
            user_id=current_user.id,
            cafe_id=cafe_id,
        )

    if show_all:
        return await get_bookings(
            db=db,
            user_id=user_id,
            cafe_id=cafe_id,
        )

    return await get_bookings(
        db=db,
        cafe_id=cafe_id,
    )
