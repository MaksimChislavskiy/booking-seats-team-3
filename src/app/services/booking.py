import logging
from datetime import date, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud, slot_crud, table_crud
from app.models import Booking, TableSlotBooking, User, UserRole
from app.schemas import BookingCreate, TableSlot
from app.services.cafe import (
    can_manage_cafe,
    ensure_cafe_is_active,
    get_cafe_or_404,
)
from app.services.user import get_user_or_404
from app.services.booking_events import on_booking_created

logger = logging.getLogger(__name__)


class BookingService:
    async def get_bookings_list(
        self,
        show_all: bool,
        cafe_id: int | None,
        user_id: int | None,
        current_user: User,
        session: AsyncSession,
    ) -> list[Booking]:
        """Возвращает список бронирований с учётом прав доступа пользователя.

        Формирует список бронирований на основе роли текущего пользователя
        и переданных параметров фильтрации.

        Правила доступа:
        - Администратор может просматривать все бронирования, с возможностью
                                            фильтрации по кафе и пользователю.
        - Менеджер может просматривать бронирования только тех кафе,
                                                которыми он управляет.
        - Обычный пользователь может просматривать только свои бронирования,
                                        независимо от переданного `user_id`.
        - Неактивные бронирования возвращаются только при `show_all=True`.

        Args:
            show_all: Если True — возвращает все бронирования,
                                        иначе только активные.
            cafe_id: Идентификатор кафе для фильтрации.
            user_id: Идентификатор пользователя для фильтрации.
            current_user: Текущий авторизованный пользователь.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Список объектов Booking, удовлетворяющих условиям фильтрации.

        Raises:
            HTTPException: Если указанное кафе или пользователь не существуют.

        """
        filters: list[dict[str, Any]] = []

        cafe = None
        if cafe_id is not None:
            cafe = await get_cafe_or_404(cafe_id=cafe_id, session=session)

        if current_user.role == UserRole.ADMIN:
            effective_show_all = show_all

            if cafe_id is not None:
                filters.append({
                    'field': 'cafe_id',
                    'op': 'eq',
                    'value': cafe_id,
                })

            if user_id is not None:
                user = await get_user_or_404(user_id=user_id, session=session)
                filters.append({
                    'field': 'user_id',
                    'op': 'eq',
                    'value': user.id,
                })

        elif cafe and can_manage_cafe(current_user, cafe.id):
            effective_show_all = show_all
            filters.append({'field': 'cafe_id', 'op': 'eq', 'value': cafe.id})

            if user_id is not None:
                user = await get_user_or_404(user_id=user_id, session=session)
                filters.append({
                    'field': 'user_id',
                    'op': 'eq',
                    'value': user.id,
                })

        else:
            effective_show_all = False

            filters.append({
                'field': 'user_id',
                'op': 'eq',
                'value': current_user.id,
            })

            if cafe_id is not None:
                filters.append({
                    'field': 'cafe_id',
                    'op': 'eq',
                    'value': cafe_id,
                })

        if not effective_show_all:
            filters.append({
                'field': 'is_active',
                'op': 'eq',
                'value': True,
            })

        return await booking_crud.get_multi(filters=filters, session=session)

    async def create_booking(
        self,
        booking_in: BookingCreate,
        user: User,
        session: AsyncSession,
    ) -> Booking:
        """Создаёт новое бронирование с привязанными столами и слотами.

        Последовательно выполняет:
        - проверку существования и активности кафе;
        - валидацию даты бронирования;
        - проверку дубликатов связок стол–слот;
        - проверку существования и доступности столов и слотов;
        - проверку отсутствия конфликтующих бронирований;
        - создание `Booking` и связанных `TableSlotBooking`.

        Args:
            booking_in: Данные для создания бронирования.
            user: Текущий пользователь.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Созданный объект Booking.

        Raises:
            HTTPException: Если данные некорректны или ресурсы заняты.

        """
        cafe = await get_cafe_or_404(
            cafe_id=booking_in.cafe_id,
            session=session,
        )

        ensure_cafe_is_active(cafe)

        self._validate_booking_date(booking_in.booking_date)

        self._validate_no_duplicate_table_slots(booking_in.tables_slots)

        await self._validate_tables_slots(
            cafe_id=cafe.id,
            tables_slots=booking_in.tables_slots,
            session=session,
        )

        await self._ensure_booking_available(
            cafe_id=cafe.id,
            booking_date=booking_in.booking_date,
            tables_slots=booking_in.tables_slots,
            session=session,
        )

        booking_data = self._prepare_booking_data(
            booking_in=booking_in,
            user_id=user.id,
        )

        table_slot_objects = self._build_table_slot_bookings(
            tables_slots=booking_in.tables_slots,
        )

        booking = await booking_crud.create(
            obj_in=booking_data,
            related={'tables_slots': table_slot_objects},
            session=session,
        )

        # TODO: позже лучше считать по слотам
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

        logger.info(
            'Создано бронирование: %s',
            booking.__repr__(),
            extra={'user': f'{user.username} id={user.id}'},
        )

        return booking

    @staticmethod
    def _validate_booking_date(booking_date: date) -> None:
        """Проверяет корректность даты бронирования.

        Args:
            booking_date: Дата, которую пользователь пытается забронировать.

        Raises:
            HTTPException: Если дата бронирования меньше текущей даты.

        """
        if booking_date < datetime.today().date():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Время бронирования не может быть в прошлом',
            )

    def _validate_no_duplicate_table_slots(
        self,
        tables_slots: list[TableSlot],
    ) -> None:
        """Проверяет отсутствие дублирующихся связок стол–слот.

        Валидирует входные данные из запроса и гарантирует,
        что каждая пара (table_id, slot_id) передана не более одного раза.

        Args:
            tables_slots: Список связок стол–слот из запроса.

        Raises:
            400: Если одна и та же пара передана более одного раза.

        """
        pairs = [
            (table_slot.table_id, table_slot.slot_id)
            for table_slot in tables_slots
        ]
        if len(pairs) != len(set(pairs)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Один и тот же стол и слот переданы более одного раза',
            )

    async def _validate_tables_slots(
        self,
        cafe_id: int,
        tables_slots: list[TableSlot],
        session: AsyncSession,
    ) -> None:
        """Проверяет существование и принадлежность столов и слотов кафе.

        Метод выполняет следующие проверки:
        - все переданные столы существуют;
        - все переданные слоты существуют;
        - столы и слоты принадлежат указанному кафе;
        - столы и слоты активны (`is_active = True`).

        Args:
            cafe_id: Идентификатор кафе, для которого выполняется бронирование.
            tables_slots: Список связок стол–слот, переданных пользователем.
            session: Асинхронная SQLAlchemy-сессия.

        Raises:
            400: Если хотя бы один слот не существует,
                    неактивен или не принадлежит кафе;
            400: Если хотя бы один стол не существует,
                    неактивен или не принадлежит кафе.

        """
        table_ids, slot_ids = self._extract_table_and_slot_ids(tables_slots)

        slots = await slot_crud.get_multi(
            filters=[
                {'field': 'id', 'op': 'in', 'value': slot_ids},
                {'field': 'cafe_id', 'op': 'eq', 'value': cafe_id},
                {'field': 'is_active', 'op': 'eq', 'value': True},
            ],
            session=session,
        )

        if len(slot_ids) != len(slots):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    'Один или несколько слотов не существуют, '
                    'или не относятся к данному кафе, или неактивны'
                ),
            )

        tables = await table_crud.get_multi(
            filters=[
                {'field': 'id', 'op': 'in', 'value': table_ids},
                {'field': 'cafe_id', 'op': 'eq', 'value': cafe_id},
                {'field': 'is_active', 'op': 'eq', 'value': True},
            ],
            session=session,
        )

        if len(table_ids) != len(tables):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    'Один или несколько столов не существуют, '
                    'или не относятся к данному кафе, или неактивны'
                ),
            )

    async def _ensure_booking_available(
        self,
        cafe_id: int,
        booking_date: date,
        tables_slots: list[TableSlot],
        *,
        exclude_booking_id: int | None = None,
        session: AsyncSession,
    ) -> None:
        """Проверяет отсутствие конфликтующих бронирований.

        Проверяет, что ни один из переданных столов не занят
        в указанный временной слот на заданную дату в рамках кафе.
        Проверка учитывает только активные бронирования
        со статусами PENDING и CONFIRMED.

        Args:
            cafe_id: Идентификатор кафе.
            booking_date: Дата бронирования.
            tables_slots: Список связок стол–слот, которые
                        пользователь пытается забронировать.
            exclude_booking_id: Идентификатор бронирования,
                        которое необходимо исключить из проверки.
            session: Асинхронная SQLAlchemy-сессия.

        Raises:
            409: Если найдено хотя бы одно конфликтующее бронирование.

        """
        table_ids, slot_ids = self._extract_table_and_slot_ids(tables_slots)

        bookings = await booking_crud.find_conflicting_bookings(
            cafe_id=cafe_id,
            booking_date=booking_date,
            table_ids=table_ids,
            slot_ids=slot_ids,
            exclude_booking_id=exclude_booking_id,
            session=session,
        )

        if bookings:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Один или несколько столов уже заняты в выбранный слот',
            )

    def _prepare_booking_data(
        self,
        booking_in: BookingCreate,
        user_id: int,
    ) -> dict:
        """Подготавливает данные для создания бронирования.

        Args:
            booking_in: Данные для создания бронирования.
            user_id: Идентификатор текущего пользователя.

        Returns:
            Словарь данных для передачи в CRUD.

        """
        data = booking_in.model_dump(exclude_unset=True)
        data['user_id'] = user_id
        return data

    def _build_table_slot_bookings(
        self,
        tables_slots: list[TableSlot],
    ) -> list[TableSlotBooking]:
        """Создаёт ORM-объекты `TableSlotBooking` из входных данных.

        Преобразует входные связки стол–слот в ORM-объекты`TableSlotBooking`,
        которые будут привязаны к объекту `Booking`.

        Args:
            tables_slots: Список связок стол–слот из запроса.

        Returns:
            Список ORM-объектов `TableSlotBooking` для передачи в CRUD.

        """
        return [
            TableSlotBooking(
                table_id=table_slot.table_id,
                slot_id=table_slot.slot_id,
            )
            for table_slot in tables_slots
        ]

    @staticmethod
    def _extract_table_and_slot_ids(
        tables_slots: list[TableSlot],
    ) -> tuple[set[int], set[int]]:
        """Извлекает идентификаторы столов и слотов для запросов к БД.

        Args:
            tables_slots: Список связок стол–слот.

        Returns:
            Кортеж из двух множеств:
            - уникальные идентификаторы столов;
            - уникальные идентификаторы слотов.

        """
        table_ids: set[int] = set()
        slot_ids: set[int] = set()

        for table_slot in tables_slots:
            table_ids.add(table_slot.table_id)
            slot_ids.add(table_slot.slot_id)

        return table_ids, slot_ids


booking_service = BookingService()
