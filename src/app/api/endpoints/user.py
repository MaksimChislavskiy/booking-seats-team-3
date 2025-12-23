import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import current_manager_or_admin, current_user
from app.core.db import get_async_session
from app.core.security import get_password_hash
from app.crud.user import user_crud
from app.models import User, UserRole
from app.schemas import UserCreate, UserInfo, UserUpdate

logger = logging.getLogger('cafe_booking')

router = APIRouter()


@router.get(
    '',
    response_model=list[UserInfo],
    summary='Получение списка пользователей',
)
async def get_users(
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(current_manager_or_admin),
) -> list[UserInfo]:
    """Возвращает список всех пользователей (admin / manager)."""
    return await user_crud.get_multi(session=session)


@router.post(
    '',
    response_model=UserInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация нового пользователя',
)
async def create_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_async_session),
) -> UserInfo:
    """Регистрирует нового пользователя."""
    logger.info(
        'User registration attempt',
        extra={'user': user_in.username},
    )

    if not user_in.email and not user_in.phone:
        logger.warning(
            'User registration failed: no email or phone',
            extra={'user': user_in.username},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Необходимо указать email или phone',
        )

    if await user_crud.get_by_username(user_in.username, session):
        logger.warning(
            'User registration failed: username already exists',
            extra={'user': user_in.username},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Username уже используется',
        )

    user = User(
        username=user_in.username,
        email=user_in.email,
        phone=user_in.phone,
        tg_id=user_in.tg_id,
        password_hash=get_password_hash(user_in.password),
        role=UserRole.USER,
        is_active=True,
    )

    created_user = await user_crud.create(user, session)

    logger.info(
        'User successfully created',
        extra={'user': created_user.username},
    )

    return created_user


@router.get(
    '/{user_id}',
    response_model=UserInfo,
    summary='Получение пользователя по ID',
)
async def get_user_by_id(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(current_manager_or_admin),
) -> UserInfo:
    """Возвращает пользователя по его ID (admin / manager)."""
    user = await user_crud.get_by_id(user_id, session)
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    return user


@router.patch(
    '/{user_id}',
    response_model=UserInfo,
    summary='Обновление пользователя по ID',
)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(current_manager_or_admin),
) -> UserInfo:
    """Обновляет данные пользователя по ID (admin / manager)."""
    user = await user_crud.get_by_id(user_id, session)
    if not user:
        logger.warning(
            'User update failed: user not found',
            extra={'user': admin.username},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден',
        )

    data = user_in.model_dump(exclude_unset=True)

    if 'password' in data:
        data['password_hash'] = get_password_hash(data.pop('password'))

    updated_user = await user_crud.update(user, data, session)

    logger.info(
        'User updated by admin',
        extra={'user': admin.username},
    )

    return updated_user


@router.get(
    '/me',
    response_model=UserInfo,
    summary='Получение текущего пользователя',
)
async def get_me(
    user: User = Depends(current_user),
) -> UserInfo:
    """Возвращает информацию о текущем пользователе."""
    return user


@router.patch(
    '/me',
    response_model=UserInfo,
    summary='Обновление текущего пользователя',
)
async def update_me(
    user_in: UserUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
) -> UserInfo:
    """Обновляет данные текущего пользователя."""
    data = user_in.model_dump(exclude_unset=True)

    if 'email' in data and data['email'] != user.email:
        if await user_crud.get_by_email_or_phone(data['email'], session):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Email уже используется',
            )

    if 'phone' in data and data['phone'] != user.phone:
        if await user_crud.get_by_email_or_phone(data['phone'], session):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Phone уже используется',
            )

    if 'password' in data:
        data['password_hash'] = get_password_hash(data.pop('password'))

    return await user_crud.update(user, data, session)
