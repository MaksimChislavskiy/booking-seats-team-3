from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.services.booking_events import on_booking_created

from app.core.db import get_async_session
from app.core.responses import (
    BAD_REQUEST_RESPONSE,
    CONFLICT_RESPONSE,
    CREATED_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    OK_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.crud import booking_crud
from app.models import User
from app.schemas import BookingCreate, BookingInfo, BookingUpdate
from app.services.auth import current_active_user
from app.services.booking import booking_service
from app.services.booking_events import on_booking_created

router = APIRouter()


@router.get(
    '/',
    response_model=list[BookingInfo],
    summary='Получение списка бронирований',
    description=(
        'Возвращает список бронирований с учетом роли пользователя.\n\n'
        '- Администратор может просматривать все бронирования с возможностью '
        'фильтрации по кафе, пользователю и статусу активности.\n'
        '- Менеджер может просматривать бронирования только тех кафе, '
        'которыми он управляет.\n'
        '- Обычный пользователь может просматривать только собственные '
        'бронирования (параметр `user_id` игнорируется).'
    ),
    responses={
        **OK_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def get_bookings_list(
    show_all: bool = Query(
        False,
        description=(
            'Показывать все бронирования или нет. '
            'По умолчанию показывает только активные бронирования.'
        ),
    ),
    cafe_id: int | None = Query(
        None,
        description=(
            'ID кафе, в котором показывать бронирования. '
            'Если не задано - показывает все бронирования во всех кафе'
        ),
    ),
    user_id: int | None = Query(
        None,
        description=(
            'ID пользователя, бронирования которого показывать. '
            'Если не задано - показывает бронирования всех пользователей'
        ),
    ),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[BookingInfo]:
    """Возвращает список бронирований с учетом прав доступа пользователя.

    Правила доступа:
    - администратор имеет полный доступ;
    - менеджер — доступ только к своим кафе;
    - пользователь — доступ только к собственным бронированиям.

    Args:
        show_all: Показывать ли неактивные бронирования.
        cafe_id: Идентификатор кафе для фильтрации.
        user_id: Идентификатор пользователя для фильтрации.
        current_user: Текущий авторизованный пользователь.
        session: Асинхронная SQLAlchemy-сессия.

    Returns:
        Список бронирований.

    Raises:
        HTTPException: Если указанное кафе или пользователь не существуют.

    """
    return await booking_service.get_bookings_list(
        show_all=show_all,
        cafe_id=cafe_id,
        user_id=user_id,
        current_user=current_user,
        session=session,
    )


@router.post(
    '/',
    response_model=BookingInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового бронирования',
    description=(
        'Создает новое бронирования. Только для авторизированных пользователей'
    ),
    responses={
        **CREATED_RESPONSE,
        **BAD_REQUEST_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **CONFLICT_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def create_booking(
    booking_in: BookingCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> BookingInfo:
    """Создаёт новое бронирование для текущего пользователя.

    Доступно любому авторизованному пользователю независимо от роли.

    Проверяется:
    - существование и активность кафе;
    - корректность даты бронирования;
    - отсутствие дубликатов связок стол–слот;
    - существование и активность столов и слотов;
    - отсутствие конфликтующих бронирований.

    Args:
        booking_in: Данные для создания бронирования.
        user: Текущий авторизованный пользователь.
        session: Асинхронная SQLAlchemy-сессия.

    Returns:
        Информация о созданном бронировании.

    Raises:
        HTTPException:
            - 400: некорректные данные или несуществующие ресурсы;
            - 401: пользователь не авторизован;
            - 409: один или несколько столов уже заняты;
            - 422: ошибка валидации входных данных.

    """
    booking = await booking_service.create_booking(
        booking_in=booking_in,
        user=user,
        session=session,
    )

    remind_at = datetime.combine(
        booking.booking_date,
        datetime.min.time(),
    )

    task_id = on_booking_created(
        booking_id=booking.id,
        remind_at=remind_at,
    )

    await booking_crud.update(
        db_obj=booking,
        obj_in={"reminder_task_id": task_id},
        session=session,
    )

    return BookingInfo.model_validate(booking)

# @router.get(
#     '/{booking_id}',
#     response_model=BookingInfo,
#     summary='Информация о бронировании',
#     description='Доступно владельцу или менеджеру кафе.',
# )
# async def get_booking(
#     booking_id: int,
#     session: AsyncSession = Depends(get_async_session),
#     current_user: User = Depends(current_active_user),
# ) -> BookingInfo:
#     """Детальная информация о бронировании."""
#     booking = await booking_crud.get_by_id(booking_id, session=session)
#     if not booking:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail='Бронирование не найдено',
#         )
#     if booking.user_id != current_user.id and current_user.role not in [
#         'admin',
#         'manager',
#     ]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail='Доступ запрещён',
#         )
#     return booking


# @router.patch(
#     '/{booking_id}',
#     response_model=BookingInfo,
#     summary='Обновить бронирование',
#     description='Обновление информации о бронировании по его ID.'
#     'Для администраторов и менеджеров - все бронирования, '
#     'для пользователей - только свои.',
# )
# async def update(
#     booking_id: int,
#     booking_in: BookingUpdate,
#     session: AsyncSession = Depends(get_async_session),
#     current_user: User = Depends(current_active_user),
# ) -> BookingInfo:
#     """Обновляет бронирование (только владелец)."""
#     booking = await booking_crud.get_by_id(booking_id, session=session)
#     if not booking:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail='Бронирование не найдено',
#         )

#     if booking.user_id != current_user.id and current_user.role not in [
#         'admin',
#         'manager',
#     ]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail='Доступ запрещён',
#         )

#     return await booking_crud.update(
#         db_obj=booking,
#         obj_in=booking_in,
#         session=session,
#     )


# TODO: Добавить deactivate_booking
