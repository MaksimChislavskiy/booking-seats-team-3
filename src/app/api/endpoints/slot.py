# app/api/endpoints/slot.py
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.responses import (
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.models import User
from app.schemas import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate
from app.services.auth import current_active_user
from app.services.slot_service import slot_service

router = APIRouter()


@router.get(
    '/',
    response_model=list[TimeSlotInfo],
    status_code=status.HTTP_200_OK,
    summary='Список временных слотов в кафе',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def get_time_slots_list(
    cafe_id: int = Path(..., description='ID кафе'),
    show_all: bool = Query(
        default=False,
        description='Показывать все слоты?',
    ),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> list[TimeSlotInfo]:
    """Получение списка временных слотов кафе."""
    return await slot_service.get_slots_list(
        session=session,
        cafe_id=cafe_id,
        show_all=show_all,
        current_user=current_user,
    )


@router.post(
    '/',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Новый временной слот в кафе',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def create_time_slot_endpoint(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_in: TimeSlotCreate = ...,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> TimeSlotInfo:
    """Создание нового временного слота."""
    return await slot_service.create_slot(
        session=session,
        cafe_id=cafe_id,
        slot_in=slot_in,
        current_user=current_user,
    )


@router.get(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_200_OK,
    summary='Информация о временном слоте в кафе по его ID',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def get_time_slot_by_id(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_id: int = Path(..., description='ID слота'),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> TimeSlotInfo:
    """Получение информации о временном слоте по ID."""
    return await slot_service.get_slot_by_id(
        session=session,
        cafe_id=cafe_id,
        slot_id=slot_id,
        current_user=current_user,
    )


@router.patch(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_200_OK,
    summary='Обновление информации о временом слоте в кафе по его ID',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def update_time_slot_endpoint(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_id: int = Path(..., description='ID слота'),
    updates: TimeSlotUpdate = ...,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> TimeSlotInfo:
    """Обновление информации о временном слоте."""
    return await slot_service.update_slot(
        session=session,
        cafe_id=cafe_id,
        slot_id=slot_id,
        updates=updates,
        current_user=current_user,
    )


@router.delete(
    '/{slot_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удаление временного слота',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def delete_time_slot_endpoint(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_id: int = Path(..., description='ID слота'),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> None:
    """Деактивация временного слота."""
    await slot_service.delete_slot(
        session=session,
        cafe_id=cafe_id,
        slot_id=slot_id,
        current_user=current_user,
    )
