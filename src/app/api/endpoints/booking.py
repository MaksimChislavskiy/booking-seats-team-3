from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.crud.booking import booking_crud
from app.models.booking import Booking, TableSlotBooking
from app.models.slot import Slot
from app.models.table import Table
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingInfo, BookingUpdate
from app.services.auth import current_active_user

router = APIRouter(prefix='/booking', tags=['Бронирования'])


@router.post(
    '/',
    response_model=BookingInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создать бронирование',
)
async def create_booking(
    booking_in: BookingCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> BookingInfo:
    """Создаёт новое бронирование."""
    if booking_in.booking_date < datetime.today().date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Дата бронирования не может быть в прошлом',
        )

    # Все столы слоты из одного кафе
    cafe_id = None
    for ts in booking_in.tables_slots:
        slot = await session.get(Slot, ts.slot_id)
        if not slot:
            raise HTTPException(404, f'Слот {ts.slot_id} не найден')
        table = await session.get(Table, ts.table_id)
        if not table:
            raise HTTPException(404, f'Стол {ts.table_id} не найден')

        if cafe_id is None:
            cafe_id = slot.cafe_id
        if slot.cafe_id != cafe_id or table.cafe_id != cafe_id:
            raise HTTPException(
                status_code=400,
                detail='Все столы и слоты должны принадлежать одному кафе',
            )

    # Нет пересечения
    for ts in booking_in.tables_slots:
        overlapping = await session.execute(
            select(Booking).join(TableSlotBooking).where(
                TableSlotBooking.table_id == ts.table_id,
                TableSlotBooking.slot_id == ts.slot_id,
                Booking.is_active,
                Booking.booking_date == booking_in.booking_date,
            ),
        )
        if overlapping.scalars().first():
            raise HTTPException(
                status_code=400,
                detail=(
                    f'Слот {ts.slot_id} на столе {ts.table_id} '
                    'уже забронирован на эту дату'
                ),
            )

    # Создание
    data = booking_in.model_dump()
    data['user_id'] = current_user.id
    data['cafe_id'] = cafe_id
    booking = await booking_crud.create(data, session=session)

    await session.refresh(
        booking,
        attribute_names=['user', 'cafe', 'tables_slots'],
    )
    return booking


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
    """Возвращает список бронирований."""
    filters = []

    if current_user.role not in ['admin', 'manager']:
        filters.append(
            {'field': 'user_id', 'op': 'eq', 'value': current_user.id},
        )
        if cafe_id is not None:
            filters.append(
                {"field": "cafe_id", "op": "eq", "value": cafe_id},
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
    "/{booking_id}",
    response_model=BookingInfo,
    summary='Информация о бронировании',
)
async def get_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> BookingInfo:
    """Детальная информация о бронировании."""
    booking = await booking_crud.get_by_id(booking_id, session=session)
    if not booking:
        raise HTTPException(404, 'Бронирование не найдено')

    if (
        booking.user_id != current_user.id
        and current_user.role not in ['admin", "manager']
    ):
        raise HTTPException(403, 'Доступ запрещён')

    return booking


@router.patch(
    "/{booking_id}",
    response_model=BookingInfo,
    summary='Обновить бронирование',
)
async def update_booking(
    booking_id: int,
    booking_in: BookingUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> BookingInfo:
    """Обновляет бронирование."""
    booking = await booking_crud.get_by_id(booking_id, session=session)
    if not booking:
        raise HTTPException(404, 'Бронирование не найдено')

    if booking.booking_date < datetime.today().date() or not booking.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Изменение активных/прошедших броней запрещено',
        )

    if booking.user_id != current_user.id and current_user.role not in [
        'admin', 'manager']:
        raise HTTPException(403, 'Доступ запрещён')

    return await booking_crud.update(
        db_obj=booking,
        obj_in=booking_in,
        session=session,
    )
