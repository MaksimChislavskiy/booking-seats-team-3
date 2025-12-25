from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_async_session
from app.crud.cafe import cafe as crud_cafe
from app.crud.slot import slot as crud_slot
from app.models.users import User
from app.schemas.slot import TimeSlotCreate, TimeSlotRead, TimeSlotUpdate

slots_router = APIRouter()


@slots_router.get(
    '/{cafe_id}/time_slots',
    response_model=List[TimeSlotRead],
    status_code=status.HTTP_200_OK,
)
async def get_time_slots_list(
    cafe_id: int = Path(..., description='ID кафе'),
    show_all: bool = Query(
        default=False,
        description='Показывать все слоты',
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description='Сколько записей пропустить',
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
        description='Лимит записей',
    ),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> List[TimeSlotRead]:
    """Получение списка временных слотов кафе.

    - Администраторы и менеджеры:
      - получают все слоты при show_all=true
      - могут видеть неактивные слоты

    - Пользователи:
      - получают только активные слоты
      - параметр show_all игнорируется
    """
    cafe = await crud_cafe.get(db, id=cafe_id)
    if not cafe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Кафе не найдено',
        )
    if not current_user.is_admin and not current_user.is_manager:
        if not cafe.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Нет доступа к неактивному кафе',
            )
        show_all = False
    return await crud_slot.get_by_cafe(
        session=db,
        cafe_id=cafe_id,
        skip=skip,
        limit=limit,
        show_all=show_all,
    )


@slots_router.post(
    '/{cafe_id}/time_slots',
    response_model=TimeSlotRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_time_slot_endpoint(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_in: TimeSlotCreate = ...,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> TimeSlotRead:
    """Создание нового временного слота.

    Только для администраторов и менеджеров.
    """
    if not current_user.is_admin and not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав',
        )
    cafe = await crud_cafe.get(db, id=cafe_id)
    if not cafe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Кафе не найдено',
        )
    if slot_in.end_time <= slot_in.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Время окончания должно быть позже времени начала',
        )
    slot_exists = await crud_slot.check_time_slot_exists(
        session=db,
        cafe_id=cafe_id,
        start_time=slot_in.start_time,
        end_time=slot_in.end_time,
    )
    if slot_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=('Слот с таким интервалом времени '
                    'уже существует в этом кафе'),
        )
    overlapping_slots = await crud_slot.get_slots_by_time_range(
        session=db,
        cafe_id=cafe_id,
        start_time=slot_in.start_time,
        end_time=slot_in.end_time,
    )
    if overlapping_slots:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Слот пересекается с существующими слотами в этом кафе',
        )
    try:
        slot_data = slot_in.model_dump()
        slot_data['cafe_id'] = cafe_id
        db_slot = await crud_slot.create_with_cafe(
            session=db,
            slot_in=TimeSlotCreate(**slot_data),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Ошибка при создании слота: {str(e)}',
        )
    return db_slot


@slots_router.get(
    '/{cafe_id}/time_slots/{slot_id}',
    response_model=TimeSlotRead,
    status_code=status.HTTP_200_OK,
)
async def get_time_slot_by_id(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_id: int = Path(..., description='ID слота'),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> TimeSlotRead:
    """Получение информации о временном слоте по ID.

    - Администраторы и менеджеры: видят все слоты
    - Пользователи: видят только активные слоты в активных кафе
    """
    slot = await crud_slot.get_by_id_and_cafe(
        session=db,
        slot_id=slot_id,
        cafe_id=cafe_id,
    )
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Временной слот не найден',
        )
    if not current_user.is_admin and not current_user.is_manager:
        cafe = await crud_cafe.get(db, id=cafe_id)
        if not cafe or not cafe.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Нет доступа к неактивному кафе',
            )
        if not slot.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Нет доступа к неактивному слоту',
            )
    return slot


@slots_router.patch(
    '/{cafe_id}/time_slots/{slot_id}',
    response_model=TimeSlotRead,
    status_code=status.HTTP_200_OK,
)
async def update_time_slot_endpoint(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_id: int = Path(..., description='ID слота'),
    updates: TimeSlotUpdate = ...,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> TimeSlotRead:
    """Обновление информации о временном слоте по ID.

    Только для администраторов и менеджеров.
    """
    if not current_user.is_admin and not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав',
        )
    slot = await crud_slot.get_by_id_and_cafe(
        session=db,
        slot_id=slot_id,
        cafe_id=cafe_id,
    )
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Временной слот не найден',
        )
    update_data = updates.model_dump(exclude_unset=True)
    if 'start_time' in update_data or 'end_time' in update_data:
        start_time = update_data.get('start_time', slot.start_time)
        end_time = update_data.get('end_time', slot.end_time)
        if end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Время окончания должно быть позже времени начала',
            )
        slot_exists = await crud_slot.check_time_slot_exists(
            session=db,
            cafe_id=cafe_id,
            start_time=start_time,
            end_time=end_time,
            exclude_slot_id=slot_id,
        )
        if slot_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=('Слот с таким интервалом времени '
                        'уже существует в этом кафе'),
            )
        overlapping_slots = await crud_slot.get_slots_by_time_range(
            session=db,
            cafe_id=cafe_id,
            start_time=start_time,
            end_time=end_time,
        )
        overlapping_slots = [s for s in overlapping_slots if s.id != slot_id]
        if overlapping_slots:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=('Обновленный слот пересекается '
                        'с другими слотами в этом кафе'),
            )
    try:
        updated_slot = await crud_slot.update_slot(
            session=db,
            db_slot=slot,
            slot_in=updates,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Ошибка при обновлении слота: {str(e)}',
        )
    return updated_slot


@slots_router.delete(
    '/{cafe_id}/time_slots/{slot_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_time_slot_endpoint(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_id: int = Path(..., description='ID слота'),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Удаление временного слота.

    Только для администраторов и менеджеров.
    Вместо физического удаления деактивирует слот.
    """
    if not current_user.is_admin and not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав',
        )
    slot = await crud_slot.get_by_id_and_cafe(
        session=db,
        slot_id=slot_id,
        cafe_id=cafe_id,
    )
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Временной слот не найден',
        )
    try:
        await crud_slot.update_slot(
            session=db,
            db_slot=slot,
            slot_in=TimeSlotUpdate(is_active=False),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Ошибка при удалении слота: {str(e)}',
        )
