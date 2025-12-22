from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.db import get_async_session
from src.app.core.dependencies import get_current_user
from src.app.crud.booking import (
    cancel_booking,
    create_booking,
    get_booking_by_id,
    get_bookings_for_cafe,
    get_bookings_list,
    update_booking,
)
from src.app.models.user import User
from src.app.schemas.booking import BookingCreate, BookingInfo, BookingUpdate

router = APIRouter()


@router.post(
    '/',
    response_model=BookingInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создать бронирование',
    description='Создаёт новое бронирование для авторизованного пользователя.',
)
async def create(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingInfo:
    """Создаёт бронирование."""
    return await create_booking(db, booking_in, user_id=current_user.id)


@router.get(
    '/',
    response_model=list[BookingInfo],
    summary='Список моих бронирований',
    description='Возвращает список бронирований текущего пользователя.',
)
async def read_my_list(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> list[BookingInfo]:
    """Список бронирований пользователя."""
    return await get_bookings_list(db, user_id=current_user.id)


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Информация о бронировании',
    description='Доступно владельцу или менеджеру кафе.',
)
async def read(
    booking_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingInfo:
    """Детальная информация о бронировании."""
    booking = await get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail='Бронирование не найдено')
    if (
        booking.user_id != current_user.id
        and current_user.role not in ['admin', 'manager']
    ):
        raise HTTPException(status_code=403, detail='Доступ запрещён')
    return booking


@router.patch(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Обновить бронирование',
    description='Можно изменить только до начала слота.',
)
async def update(
    booking_id: int,
    booking_in: BookingUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingInfo:
    """Обновляет бронирование (только владелец)."""
    booking = await get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail='Бронирование не найдено')
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Доступ запрещён')
    return await update_booking(db, booking, booking_in)


@router.delete(
    '/{booking_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Отменить бронирование',
)
async def cancel(
    booking_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Отменяет бронирование (только владелец)."""
    booking = await get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail='Бронирование не найдено')
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Доступ запрещён')
    await cancel_booking(db, booking)


@router.get(
    '/cafe/{cafe_id}',
    response_model=list[BookingInfo],
    summary='Бронирования кафе',
    description='Для менеджеров кафе.',
)
async def read_cafe_bookings(
    cafe_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> list[BookingInfo]:
    """Список бронирований для кафе (менеджер/админ)."""
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail='Доступ запрещён')
    return await get_bookings_for_cafe(db, cafe_id=cafe_id)
