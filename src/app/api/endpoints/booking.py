from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.crud.booking import booking_crud
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingInfo, BookingUpdate
from app.services.auth import get_current_user

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
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingInfo:
    """Создаёт бронирование."""
    return await booking_crud.create(
        session,
        booking_in,
        user_id=current_user.id,
    )


@router.get(
    '/',
    response_model=list[BookingInfo],
    summary='Список моих бронирований',
    description='Возвращает список бронирований текущего пользователя.',
)
async def read_my_list(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> list[BookingInfo]:
    """Список бронирований пользователя."""
    return await booking_crud.get_multi(
        session,
        user_id=current_user.id,
    )


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Информация о бронировании',
    description='Доступно владельцу или менеджеру кафе.',
)
async def read(
    booking_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingInfo:
    """Детальная информация о бронировании."""
    booking = await booking_crud.get(session, booking_id)
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
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BookingInfo:
    """Обновляет бронирование (только владелец)."""
    booking = await booking_crud.get(session, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail='Бронирование не найдено')
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='Доступ запрещён')
    return await booking_crud.update(session, booking, booking_in)
