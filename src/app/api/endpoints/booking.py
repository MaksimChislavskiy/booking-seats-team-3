from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.crud import booking_crud
from app.models import User
from app.schemas import BookingCreate, BookingInfo, BookingUpdate
from app.services.auth import current_active_user

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
    current_user: User = Depends(current_active_user),
) -> BookingInfo:
    """Создаёт бронирование."""
    data = booking_in.model_dump()
    data['user_id'] = current_user.id
    return await booking_crud.create(data, session=session)


@router.get(
    '/',
    response_model=list[BookingInfo],
    summary='Получение списка бронирований',
)
async def list_bookings(
    show_all: bool = False,
    cafe_id: int | None = None,
    user_id: int | None = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> list[BookingInfo]:
    filters = []

    if current_user.role not in ['admin', 'manager']:
        filters.append(
            {'field': 'user_id', 'op': 'eq', 'value': current_user.id},
        )
        if cafe_id is not None:
            filters.append(
                {'field': 'cafe_id', 'op': 'eq', 'value': cafe_id},
            )
    else:
        if not show_all:
            filters.append(
                {'field': 'user_id', 'op': 'eq', 'value': current_user.id},
            )
        if cafe_id is not None:
            filters.append(
                {'field': 'cafe_id', 'op': 'eq', 'value': cafe_id},
            )
        if user_id is not None:
            filters.append(
                {'field': 'user_id', 'op': 'eq', 'value': user_id},
            )

    return await booking_crud.get_multi(
        filters=filters or None,
        session=session,
    )


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Информация о бронировании',
    description='Доступно владельцу или менеджеру кафе.',
)
async def get_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> BookingInfo:
    """Детальная информация о бронировании."""
    booking = await booking_crud.get_by_id(session, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Бронирование не найдено',
        )
    if (
        booking.user_id != current_user.id
        and current_user.role not in ['admin', 'manager']
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Доступ запрещён',
        )
    return booking


@router.patch(
    '/{booking_id}',
    response_model=BookingInfo,
    summary='Обновить бронирование',
    description='Обновление информации о бронировании по его ID.'
    'Для администраторов и менеджеров - все бронирования, '
    'для пользователей - только свои.',
)
async def update(
    booking_id: int,
    booking_in: BookingUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> BookingInfo:
    """Обновляет бронирование (только владелец)."""
    booking = await booking_crud.get_by_id(booking_id, session=session)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Бронирование не найдено',
        )

    if booking.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Доступ запрещён',
        )

    return await booking_crud.update(
        db_obj=booking,
        obj_in=booking_in,
        session=session,
    )
