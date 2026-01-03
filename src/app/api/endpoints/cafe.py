from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.crud.cafe import cafe_crud
from app.models.user import User
from app.schemas.cafe import CafeCreate, CafeInfo, CafeUpdate
from app.services.auth import current_active_user, current_admin_or_manager

router = APIRouter()


@router.post(
    '/',
    response_model=CafeInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового кафе',
    description='Создаёт новое кафе. Только для администраторов и менеджеров.',
    responses={
        400: {'description': 'Неверные данные или кафе уже существует'},
        401: {'description': 'Не авторизован'},
        403: {'description': 'Недостаточно прав'},
        422: {'description': 'Ошибка валидации'},
    },
    dependencies=[Depends(current_admin_or_manager)],
)
async def create(
    cafe_in: CafeCreate,
    session: AsyncSession = Depends(get_async_session),
) -> CafeInfo:
    """Создаёт новое кафе."""
    # Проверка уникальности name + address
    existing = await cafe_crud.get_multi(
        session,
        filters=[
            {"field": "name", "op": "eq", "value": cafe_in.name},
            {"field": "address", "op": "eq", "value": cafe_in.address},
        ],
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Кафе с таким названием и адресом уже существует',
        )
    return await cafe_crud.create(cafe_in, session=session)


@router.get(
    '/',
    response_model=list[CafeInfo],
    summary='Получение списка кафе',
    description=(
        'Для авторизованных пользователей. '
        'Для администраторов и менеджеров — все кафе, '
        'для остальных — только активные.'
    ),
    responses={
        401: {'description': 'Не авторизован'},
        422: {'description': 'Ошибка валидации'},
    },
)
async def read_list(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> list[CafeInfo]:
    """Возвращает список кафе."""
    if current_user.role in ['admin', 'manager']:
        return await cafe_crud.get_multi(session)
    return await cafe_crud.get_multi(session, is_active=True)


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Получение информации о кафе по ID',
    description=(
        'Для авторизованных пользователей. '
        'Для администраторов и менеджеров — любое кафе, '
        'для остальных — только активное.'
    ),
    responses={
        401: {'description': 'Не авторизован'},
        403: {'description': 'Доступ запрещён'},
        404: {'description': 'Кафе не найдено'},
        422: {'description': 'Ошибка валидации'},
    },
)
async def read(
    cafe_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
) -> CafeInfo:
    """Возвращает информацию о кафе."""
    cafe = await cafe_crud.get_by_id(cafe_id, session=session)
    if not cafe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Кафе не найдено',
        )
    if current_user.role not in ['admin', 'manager'] and not cafe.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Доступ запрещён',
        )
    return cafe


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Обновление информации о кафе по ID',
    description=(
        'Частичное обновление данных кафе. '
        'Только для администраторов и менеджеров.'
    ),
    responses={
        400: {'description': 'Неверные данные'},
        401: {'description': 'Не авторизован'},
        403: {'description': 'Недостаточно прав'},
        404: {'description': 'Кафе не найдено'},
        422: {'description': 'Ошибка валидации'},
    },
    dependencies=[Depends(current_admin_or_manager)],
)
async def update(
    cafe_id: int,
    cafe_in: CafeUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> CafeInfo:
    """Обновляет данные кафе."""
    cafe = await cafe_crud.get_by_id(cafe_id, session=session)
    if not cafe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Кафе не найдено',
        )
    return await cafe_crud.update(cafe, cafe_in, session=session)
