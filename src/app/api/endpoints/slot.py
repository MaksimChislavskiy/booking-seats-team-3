from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth import get_current_user
from app.core.db import get_async_session
# from app.crud.cafe import cafe_crud
from app.crud.slot import slot_crud
from app.models.enum import UserRole
from app.models.user import User
from app.schemas.slot import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate

router = APIRouter()


@router.get(
    '/',
    response_model=List[TimeSlotInfo],
    status_code=status.HTTP_200_OK,
)
async def get_time_slots_list(
    cafe_id: int = Path(..., description='ID кафе'),
    show_all: bool = Query(
        default=False,
        description='Показывать все слоты',
    ),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> List[TimeSlotInfo]:
    """Получение списка временных слотов кафе.

    - Администраторы и менеджеры:
      - получают все слоты при show_all=true
      - могут видеть неактивные слоты

    - Пользователи:
      - получают только активные слоты
      - параметр show_all игнорируется
    """
    cafe = await cafe_crud.get(db, id=cafe_id)
    if not cafe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Кафе не найдено',
        )
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        if not cafe.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Нет доступа к неактивному кафе',
            )
        show_all = False
    return await slot_crud.get_cafe_slots(
        session=db,
        cafe_id=cafe_id,
        show_all=show_all,
    )


@router.post(
    '/',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_201_CREATED,
)
async def create_time_slot_endpoint(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_in: TimeSlotCreate = ...,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> TimeSlotInfo:
    """Создание нового временного слота.

    Только для администраторов и менеджеров.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав',
        )
    cafe = await cafe_crud.get(db, id=cafe_id)
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
    slot_exists = await slot_crud.check_time_slot_exists(
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
    overlapping_slots = await slot_crud.get_slots_by_time_range(
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
        db_slot = await slot_crud.create_with_cafe(
            session=db,
            slot_in=TimeSlotCreate(**slot_data),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Ошибка при создании слота: {str(e)}',
        )
    return db_slot


@router.get(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_200_OK,
)
async def get_time_slot_by_id(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_id: int = Path(..., description='ID слота'),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> TimeSlotInfo:
    """Получение информации о временном слоте по ID.

    - Администраторы и менеджеры: видят все слоты
    - Пользователи: видят только активные слоты в активных кафе
    """
    slot = await slot_crud.get_by_id_and_cafe(
        session=db,
        slot_id=slot_id,
        cafe_id=cafe_id,
    )
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Временной слот не найден',
        )
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        cafe = await cafe_crud.get(db, id=cafe_id)
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


@router.patch(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_200_OK,
)
async def update_time_slot_endpoint(
    cafe_id: int = Path(..., description='ID кафе'),
    slot_id: int = Path(..., description='ID слота'),
    updates: TimeSlotUpdate = ...,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> TimeSlotInfo:
    """Обновление информации о временном слоте по ID.

    Только для администраторов и менеджеров.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав',
        )
    slot = await slot_crud.get_by_id_and_cafe(
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
        slot_exists = await slot_crud.check_time_slot_exists(
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
        overlapping_slots = await slot_crud.get_slots_by_time_range(
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
        updated_slot = await slot_crud.update_slot(
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


@router.delete(
    '/{slot_id}',
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
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав',
        )
    slot = await slot_crud.get_by_id_and_cafe(
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
        await slot_crud.update_slot(
            session=db,
            db_slot=slot,
            slot_in=TimeSlotUpdate(is_active=False),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Ошибка при удалении слота: {str(e)}',
        )
