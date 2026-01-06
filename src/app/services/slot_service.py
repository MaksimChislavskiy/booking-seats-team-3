# app/services/slot_service.py
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import cafe_crud, slot_crud
from app.models import User, UserRole
from app.schemas import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate


class SlotService:
    """Сервис для управления временными слотами в кафе.

    Отвечает за бизнес-логику работы с временными слотами:
    - создание, чтение, обновление и деактивацию слотов
    - проверку прав доступа пользователей
    - валидацию временных интервалов
    - контроль пересечений слотов
    """

    async def get_slots_list(
        self,
        session: AsyncSession,
        cafe_id: int,
        show_all: bool,
        current_user: User,
    ) -> list[TimeSlotInfo]:
        """Получение списка временных слотов с учетом ролей."""
        cafe = await cafe_crud.get_by_id(session, id=cafe_id)
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
            session=session,
            cafe_id=cafe_id,
            show_all=show_all,
        )

    async def create_slot(
        self,
        session: AsyncSession,
        cafe_id: int,
        slot_in: TimeSlotCreate,
        current_user: User,
    ) -> TimeSlotInfo:
        """Создание нового временного слота."""
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Недостаточно прав',
            )
        cafe = await cafe_crud.get_by_id(session, id=cafe_id)
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
            session=session,
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
            session=session,
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
            return await slot_crud.create_with_cafe(
                session=session,
                slot_in=TimeSlotCreate(**slot_data),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Ошибка при создании слота: {str(e)}',
            )

    async def get_slot_by_id(
        self,
        session: AsyncSession,
        cafe_id: int,
        slot_id: int,
        current_user: User,
    ) -> TimeSlotInfo:
        """Получение слота по ID с проверкой прав."""
        slot = await slot_crud.get_by_id_and_cafe(
            session=session,
            slot_id=slot_id,
            cafe_id=cafe_id,
        )
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Временной слот не найден',
            )
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            cafe = await cafe_crud.get_by_id(session, id=cafe_id)
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

    async def update_slot(
        self,
        session: AsyncSession,
        cafe_id: int,
        slot_id: int,
        updates: TimeSlotUpdate,
        current_user: User,
    ) -> TimeSlotInfo:
        """Обновление информации о временном слоте."""
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Недостаточно прав',
            )
        slot = await slot_crud.get_by_id_and_cafe(
            session=session,
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
                session=session,
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
                session=session,
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
            return await slot_crud.update_slot(
                session=session,
                db_slot=slot,
                slot_in=updates,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Ошибка при обновлении слота: {str(e)}',
            )

    async def delete_slot(
        self,
        session: AsyncSession,
        cafe_id: int,
        slot_id: int,
        current_user: User,
    ) -> None:
        """Деактивация временного слота."""
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Недостаточно прав',
            )
        slot = await slot_crud.get_by_id_and_cafe(
            session=session,
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
                session=session,
                db_slot=slot,
                slot_in=TimeSlotUpdate(is_active=False),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Ошибка при удалении слота: {str(e)}',
            )


slot_service = SlotService()
