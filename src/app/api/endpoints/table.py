import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.db import get_async_session
from app.core.user import current_manager_or_admin, current_user
from app.crud.table import table_crud
from app.models import Table, User, UserRole
from app.schemas import TableCreate, TableInfo, TableUpdate
from app.validators.table import check_cafe_exists

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    '/{table_id}',
    response_model=TableInfo,
    summary='Получение информации о столе в кафе по его ID.',
    description='Для администраторов и менеджеров - все столы, '
                'для пользователей - только активные.',
)
async def get_table(
    cafe_id: int,
    table_id: int,
    current_user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Получение информации о столе с учётом прав пользователя."""
    logger.info(
        'Запрос стола. cafe_id=%d, table_id=%d, user_id=%d, role=%s',
        cafe_id, table_id, current_user.id, current_user.role.value,
        extra={
            'cafe_id': cafe_id,
            'table_id': table_id,
            'user_id': current_user.id,
            'user_role': current_user.role.value,
        },
    )
    cafe = await check_cafe_exists(cafe_id, session)
    logger.debug(
        'Кафе найдено. cafe_id=%d', cafe_id, extra={'cafe_id': cafe_id})
    table = await table_crud.get_by_id_id_active(
        session=session,
        cafe_id=cafe.id,
        table_id=table_id,
        user_role=current_user.role,
    )
    if not table:
        logger.warning(
            'Стол не найден. cafe_id=%d, table_id=%d, user_id=%d',
            cafe_id, table_id, current_user.id,
            extra={
                'cafe_id': cafe_id,
                'table_id': table_id,
                'user_id': current_user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Стол {table_id} не найден.',
        )
    logger.info(
        'Стол возвращён. cafe_id=%d, table_id=%d, is_active=%s',
        cafe_id, table_id, table.is_active,
        extra={
            'cafe_id': cafe_id,
            'table_id': table_id,
            'is_active': table.is_active,
        },
    )
    return table


@router.patch(
    '/{table_id}',
    response_model=TableInfo,
    dependencies=[Depends(current_manager_or_admin)],
    summary='Обновление информации о столе в кафе по его ID.',
    description='Обновляет только переданные поля. Для ADMIN и MANAGER.',
)
async def update_table(
    cafe_id: int,
    table_id: int,
    update_data: TableUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Обновление информации о столе (для администраторов и менеджеров)."""
    logger.info(
        'Обновление стола. cafe_id=%d, table_id=%d, data=%s',
        cafe_id, table_id, update_data.model_dump_json(),
        extra={
            'cafe_id': cafe_id,
            'table_id': table_id,
            'update_data': update_data.model_dump(),
        },
    )
    cafe = await check_cafe_exists(cafe_id, session)
    logger.debug(
        'Кафе найдено. cafe_id=%d', cafe_id, extra={'cafe_id': cafe_id})
    table = await table_crud.get_by_id_id(
        session=session,
        cafe_id=cafe.id,
        table_id=table_id,
    )
    if not table:
        logger.warning(
            'Стол не найден при обновлении. cafe_id=%d, table_id=%d',
            cafe_id, table_id,
            extra={'cafe_id': cafe_id, 'table_id': table_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Стол {table_id} не найден.',
        )
    try:
        updated_table = await table_crud.update(
            db_obj=table,
            obj_in=update_data,
            session=session,
        )
        logger.info(
            'Стол обновлён. cafe_id=%d, table_id=%d',
            cafe_id, table_id,
            extra={'cafe_id': cafe_id, 'table_id': table_id},
        )
    except ValidationError as e:
        logger.error(
            'Ошибка валидации данных. cafe_id=%d, table_id=%d, ошибка=%s',
            cafe_id, table_id, str(e),
            extra={'cafe_id': cafe_id,
                   'table_id': table_id,
                   'error': e.errors(),
                   },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Некорректные данные. Проверьте поля.",
        )
    except IntegrityError as e:
        logger.error(
            'Ошибка целостности данных БД. cafe_id=%d, table_id=%d, ошибка=%s',
            cafe_id, table_id, str(e),
            extra={'cafe_id': cafe_id,
                   'table_id': table_id,
                   'error': repr(e),
                   },
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Конфликт данных. Проверьте входные параметры.",
        )
    except OperationalError as e:
        logger.error(
            'Операционная ошибка БД. cafe_id=%d, table_id=%d, ошибка=%s',
            cafe_id, table_id, str(e),
            extra={'cafe_id': cafe_id,
                   'table_id': table_id,
                   'error': repr(e),
                   },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Временная ошибка сервиса. Попробуйте позже.",
        )
    except Exception as e:  # Крайний случай — неизвестные ошибки.
        logger.exception(
            'Неожиданная ошибка при обновлении стола. cafe_id=%d, table_id=%d',
            cafe_id, table_id,
            extra={'cafe_id': cafe_id,
                   'table_id': table_id,
                   'error': repr(e),
                   },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера.",
        )
    return updated_table


@router.post(
    '',
    response_model=TableInfo,
    dependencies=[Depends(current_manager_or_admin)],
    summary='Создаёт новый стол в кафе с указанными параметрами.',
    description='Доступно только для ADMIN и MANAGER.',
)
async def create_table(
    cafe_id: int,
    data: TableCreate,
    session: AsyncSession = Depends(get_async_session),
) -> Table:
    """Новый стол в кафе (для администраторов и менеджеров)."""
    logger.info(
        'Создание стола. cafe_id=%d, data=%s',
        cafe_id, data.model_dump_json(),
        extra={
            'cafe_id': cafe_id,
            'create_data': data.model_dump(),
        },
    )
    await check_cafe_exists(cafe_id, session)
    logger.debug(
        'Кафе существует. cafe_id=%d', cafe_id, extra={'cafe_id': cafe_id})
    new_table = await table_crud.create(
        obj_in=data,
        session=session,
        )
    logger.info(
        'Стол создан. cafe_id=%d, table_id=%d',
        cafe_id, new_table.id,
        extra={'cafe_id': cafe_id, 'table_id': new_table.id},
    )
    return new_table


@router.get(
    '',
    response_model=list[TableInfo],
    summary='Получение списка доступных для бронирования столов в кафе.',
    description='Для администраторов и менеджеров - все столы, '
                'для пользователей - только активные.',
)
async def list_tables(
    cafe_id: int,
    show_all: bool = Query(default=False),
    current_user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[Table]:
    """Список столов с учётом прав пользователя и выбором полного списка."""
    logger.info(
        'Список столов. cafe_id=%d, show_all=%s, user_id=%d, role=%s',
        cafe_id, show_all, current_user.id, current_user.role.value,
        extra={'cafe_id': cafe_id,
               'show_all': show_all,
               'user_id': current_user.id,
               'user_role': current_user.role.value,
               },
    )
    await check_cafe_exists(cafe_id, session)
    logger.debug(
        'Кафе существует. cafe_id=%d', cafe_id, extra={'cafe_id': cafe_id})
    can_show_all = current_user.role in {UserRole.ADMIN, UserRole.MANAGER}
    if show_all and can_show_all:
        logger.debug(
            'Администратор/менеджер запрашивает список всех столов cafe_id=%d',
            cafe_id,
            extra={'cafe_id': cafe_id, 'user_id': current_user.id},
        )
        filters = [
            {'field': 'cafe_id', 'op': 'eq', 'value': cafe_id},
        ]
    else:
        logger.debug(
            'Пользователь запрашивает активные столы. cafe_id=%d, role=%s',
            cafe_id, current_user.role.value,
            extra={
                'cafe_id': cafe_id,
                'user_id': current_user.id,
                'user_role': current_user.role.value,
            },
        )
        filters = [
            {'field': 'cafe_id', 'op': 'eq', 'value': cafe_id},
            {'field': 'is_active', 'op': 'eq', 'value': True},
        ]
    tables = await table_crud.get_multi(filters=filters, session=session)
    logger.info(
        'Возвращён список столов. cafe_id=%d, count=%d, show_all=%s, role=%s',
        cafe_id, len(tables), show_all, current_user.role.value,
        extra={
            'cafe_id': cafe_id,
            'tables_count': len(tables),
            'show_all': show_all,
            'user_role': current_user.role.value,
        },
    )
    return tables
