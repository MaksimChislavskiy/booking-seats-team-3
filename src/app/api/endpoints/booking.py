from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.auth import get_current_user
# переделаю когда будет аутентификация
from app.crud.bookings import (
    get_booking,
    get_bookings,
    create_booking,
    update_booking,
)
from app.models.users import User
from app.schemas.booking import BookingRead, BookingCreate, BookingUpdate

bookings_router = APIRouter()


@bookings_router.get(
    '',
    response_model=List[BookingRead],
    status_code=status.HTTP_200_OK,
)
async def get_booking_list(
    show_all: bool = Query(
        default=False,
        description='Показывать все бронирования',
    ),
    cafe_id: Optional[int] = Query(
        default=None,
        description='ID кафе',
    ),
    user_id: Optional[int] = Query(
        default=None,
        description='ID пользователя',
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


@bookings_router.post(
    '',
    response_model=BookingRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking_endpoint(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingRead:
    """
    Создание нового бронирования.

    Только для авторизованных пользователей.
    """

    if not booking_in.tables_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Необходимо указать хотя бы один слот',
        )

    booking = await create_booking(
        db=db,
        booking_in=booking_in,
        user_id=current_user.id,
    )
    return booking


@bookings_router.get(
    '/{booking_id}',
    response_model=BookingRead,
    status_code=status.HTTP_200_OK,
)
async def get_booking_by_id(
    booking_id: int = Path(..., description='ID бронирования'),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingRead:
    """
    Получение информации о бронировании по ID.

    - Администраторы и менеджеры: видят все бронирования
    - Обычные пользователи: видят только свои
    """

    booking = await get_booking(db=db, booking_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Бронирование не найдено',
        )

    if not current_user.is_admin and not current_user.is_manager:
        if booking.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Доступ запрещён',
            )

    return booking


@bookings_router.patch(
    '/{booking_id}',
    response_model=BookingRead,
    status_code=status.HTTP_200_OK,
)
async def update_booking_endpoint(
    booking_id: int = Path(..., description='ID бронирования'),
    updates: BookingUpdate = ...,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingRead:
    """
    Обновление информации о бронировании по ID.

    - Администраторы и менеджеры видят все бронирования
    - Обычные пользователи видят только свои
    """

    booking = await get_booking(db=db, booking_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Бронирование не найдено',
        )

    if not current_user.is_admin and not current_user.is_manager:
        if booking.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Доступ запрещён',
            )

    if (
        updates.booking_date
        and updates.booking_date < date.today()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Нельзя установить дату в прошлом',
        )

    updated_booking = await update_booking(
        db=db, booking_id=booking_id, updates=updates
    )
    if not updated_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Не удалось обновить бронирование',
        )

    return updated_booking
