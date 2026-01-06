from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import cafe_crud, user_crud
from app.models import Cafe, User, UserRole
from app.schemas import CafeCreate
from app.schemas.cafe import CafeUpdate


class CafeService:
    """Сервис бизнес-логики для работы с кафе.

    Отвечает за:
    - проверку прав доступа пользователей;
    - создание и обновление кафе;
    - управление менеджерами кафе;
    - контроль уникальности данных;
    - формирование бизнес-правил доступа к данным.

    Используется API-эндпоинтами как единственная точка
    доступа к логике работы с кафе.
    """

    async def get_cafe_by_id_for_user(
        self,
        cafe_id: int,
        user: User,
        session: AsyncSession,
    ) -> Cafe:
        """Возвращает кафе по ID с учётом прав пользователя.

        Правила доступа:
        - ADMIN:
            * может получить любое кафе.
        - MANAGER:
            * может получить активное кафе;
            * может получить своё кафе независимо от статуса.
        - USER:
            * может получить только активное кафе.

        Args:
            cafe_id: Идентификатор кафе.
            user: Текущий пользователь.
            session: Асинхронная сессия SQLAlchemy.

        Returns:
            Объект Cafe.

        Raises:
            HTTPException:
                - 404: если кафе не найдено;
                - 403: если доступ запрещён.

        """
        cafe = await self.get_cafe_or_404(cafe_id, session)

        if user.role == UserRole.ADMIN:
            return cafe

        if user.role == UserRole.MANAGER:
            if cafe.is_active or cafe.id == user.cafe_id:
                return cafe

        if user.role == UserRole.USER:
            if cafe.is_active:
                return cafe

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав для доступа к кафе',
        )

    async def get_cafes_for_user(
        self,
        user: User,
        show_all: bool,
        session: AsyncSession,
    ) -> list[Cafe]:
        """Возвращает список кафе с учётом роли пользователя.

        Правила:
        - ADMIN:
            * может получить все кафе;
            * `show_all` управляет показом неактивных кафе.
        - MANAGER:
            * видит все активные кафе;
            * видит своё кафе независимо от статуса.
        - USER:
            * видит только активные кафе.

        Args:
            user: Текущий аутентифицированный пользователь.
            show_all: Флаг показа неактивных кафе (учитывается
                только для администратора).
            session: Асинхронная сессия SQLAlchemy.

        Returns:
            Список объектов Cafe, доступных пользователю
            в соответствии с его ролью.

        """
        if user.role == UserRole.ADMIN:
            return await cafe_crud.get_cafes(show_all, session=session)

        if user.role == UserRole.MANAGER:
            return await cafe_crud.get_active_and_own_cafes(
                cafe_id=user.cafe_id,
                session=session,
            )

        return await cafe_crud.get_active_cafes(session=session)

    async def create_cafe(
        self,
        cafe_in: CafeCreate,
        session: AsyncSession,
    ) -> Cafe:
        """Создаёт кафе и назначает менеджеров.

        Правила:
        - Кафе может создать только администратор.
        - Список `managers_id` обязателен.
        - Все менеджеры должны:
            * существовать,
            * иметь роль MANAGER,
            * не быть привязаны к другому кафе.
        - Операция выполняется атомарно.

        Args:
            cafe_in: Данные для создания кафе.
            session: Асинхронная сессия SQLAlchemy.

        Returns:
            Созданный объект Cafe с назначенными менеджерами.

        """
        # await self._check_cafe_uniqueness(cafe_in, session)
        await self._check_existing_cafe(
            name=cafe_in.name,
            address=cafe_in.address,
            session=session,
        )
        managers = await self._get_and_validate_managers(
            cafe_in.managers_id,
            session=session,
        )
        cafe = await cafe_crud.create(cafe_in, session=session)

        self._assign_managers_to_cafe(managers, cafe.id, session=session)

        await session.commit()
        await session.refresh(cafe)

        return cafe

    async def update_cafe(
        self,
        cafe_id: int,
        cafe_in: CafeUpdate,
        session: AsyncSession,
    ) -> Cafe:
        # TODO: Добавить докстринг
        cafe = await self.get_cafe_or_404(cafe_id, session)

        if cafe_in.name or cafe_in.address:
            await self._check_existing_cafe(
                name=cafe_in.name or cafe.name,
                address=cafe_in.address or cafe.address,
                exclude_id=cafe.id,
                session=session,
            )

        cafe = await cafe_crud.update(
            db_obj=cafe,
            obj_in=cafe_in,
            session=session,
        )

        if cafe_in.managers_id is not None:
            managers = await self._get_and_validate_managers(
                cafe_in.managers_id,
                session=session,
            )
            self._update_cafe_managers(
                cafe=cafe,
                new_managers=managers,
                session=session,
            )

        await session.commit()
        await session.refresh(cafe)

        return cafe

    async def get_cafe_or_404(
        self,
        cafe_id: int,
        session: AsyncSession,
    ) -> Cafe:
        """Возвращает кафе по ID или выбрасывает 404.

        Args:
            cafe_id: Идентификатор кафе.
            session: Асинхронная сессия SQLAlchemy.

        Returns:
            Объект Cafe.

        Raises:
            HTTPException: Если кафе не найдено.

        """
        cafe = await cafe_crud.get_by_id(cafe_id, session)

        if not cafe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Кафе не найдено',
            )
        return cafe

    # FIXME: Уточнить для update метода, разрешить менеджеров,
    # FIXME: которые уже привязаны к текущему кафе
    async def _get_and_validate_managers(
        self,
        managers_id: list[int],
        session: AsyncSession,
    ) -> list[User]:
        """Получает и валидирует менеджеров по списку идентификаторов.

        Проверяет, что:
        - все переданные пользователи существуют,
        - имеют роль MANAGER,
        - не привязаны к другому кафе.

        Args:
            managers_id: Список идентификаторов менеджеров.
            session: Асинхронная сессия SQLAlchemy.

        Returns:
            Список пользователей с ролью MANAGER.

        Raises:
            HTTPException: Если хотя бы один менеджер невалиден.

        """
        managers: list[User] = await user_crud.get_managers_by_ids(
            managers_id,
            session=session,
        )

        if len(managers) != len(managers_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    'Один или несколько менеджеров не существуют '
                    'или не являются менеджерами'
                ),
            )

        for manager in managers:
            if manager.cafe_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        'Один или несколько менеджеров уже привязаны к кафе'
                    ),
                )

        return managers

    @staticmethod
    def _assign_managers_to_cafe(
        managers: list[User],
        cafe_id: int,
        session: AsyncSession,
    ) -> None:
        """Назначает менеджеров указанному кафе.

        Устанавливает `cafe_id` для каждого менеджера
        и добавляет изменения в текущую сессию.

        Args:
            managers: Список пользователей-менеджеров.
            cafe_id: Идентификатор кафе.
            session: Асинхронная сессия SQLAlchemy.

        """
        for manager in managers:
            manager.cafe_id = cafe_id
            session.add(manager)

    def _update_cafe_managers(
        self,
        cafe: Cafe,
        new_managers: list[User],
        session: AsyncSession,
    ) -> None:
        current_managers: list[User] = cafe.managers

        current_ids = {user.id for user in current_managers}
        new_ids = {user.id for user in new_managers}

        for manager in current_managers:
            if manager.id not in new_ids:
                manager.cafe_id = None
                session.add(manager)

        for manager in new_managers:
            if manager.id not in current_ids:
                manager.cafe_id = cafe.id
                session.add(manager)

    async def _check_cafe_uniqueness(  # FIXME: Удалить из-за ненадобности
        self,
        cafe_in: CafeCreate,
        session: AsyncSession,
    ) -> None:
        """Проверяет, что кафе с таким названием и адресом не существует.

        Args:
            cafe_in: Данные для создания кафе.
            session: Асинхронная сессия SQLAlchemy.

        Raises:
            HTTPException: Если кафе с таким названием и адресом уже существует

        """
        cafe = await cafe_crud.get_by_name_and_address(
            name=cafe_in.name,
            address=cafe_in.address,
            session=session,
        )
        if cafe:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Кафе с таким названием и адресом уже существует',
            )

    async def _check_existing_cafe(
        self,
        name: str,
        address: str,
        exclude_id: int | None = None,
        *,
        session: AsyncSession,
    ) -> None:
        """Проверяет уникальность кафе по (name, address).

        Args:
            name: Название кафе.
            address: Адрес кафе.
            exclude_id: ID кафе, которое нужно исключить из проверки
                (используется при обновлении).
            session: Асинхронная сессия SQLAlchemy.

        Raises:
            HTTPException: Если кафе с таким названием и адресом уже существует

        """
        cafe = await cafe_crud.get_by_name_and_address(
            name=name,
            address=address,
            session=session,
        )

        if cafe and cafe.id != exclude_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Кафе с таким названием и адресом уже существует',
            )


cafe_service = CafeService()
