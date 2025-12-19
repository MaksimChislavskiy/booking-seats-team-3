from typing import Any, Generic, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import ColumnElement, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base

ModelType = TypeVar('ModelType', bound=Base)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый класс для CRUD операций.

    Предоставляет общие методы для работы с моделями базы данных,
    включая получение, создание, обновление и мягкое удаление объектов.

    Attributes:
        model: Класс модели SQLAlchemy.

    """

    def __init__(self, model: Type[ModelType]) -> None:
        """Инициализация CRUD класса для конкретной модели."""
        self.model = model

    async def get_by_id(
        self,
        obj_id: int,
        session: AsyncSession,
    ) -> ModelType | None:
        """Возвращает объект модели по его ID.

        Args:
            obj_id: Идентификатор объекта.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Объект модели или None, если объект не найден.

        """
        stmt = select(self.model).where(self.model.id == obj_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        filters: list[dict[str, Any]] | None = None,
        *,
        session: AsyncSession,
    ) -> list[ModelType]:
        """Возвращает список объектов модели с поддержкой AND / OR фильтрации.

        Поддерживаемые форматы фильтров:

        1. Обычное условие (AND по умолчанию):
            {
                "field": str,   # имя поля модели
                "op": str,      # операция (eq, like, gt, lt, gte, lte, in)
                "value": Any,   # значение для сравнения
            }

        2. OR-группа условий:
            {
                "logic": "or",
                "conditions": [
                    {"field": "...", "op": "...", "value": ...},
                    {"field": "...", "op": "...", "value": ...},
                ]
            }

        Все элементы верхнего уровня объединяются через AND.
        OR применяется только внутри соответствующей группы.

        Args:
            filters: Список описаний фильтров или None.
            session: Асинхронная SQLAlchemy-сессия.

        Returns:
            Список объектов модели.

        """
        stmt = select(self.model)

        if filters:
            expressions: list[ColumnElement[bool]] = []

            for item in filters:
                if item.get('logic') == 'or':
                    conditions = item.get('conditions')

                    if not conditions:
                        raise ValueError('OR-группа не может быть пустой.')

                    or_expressions = [
                        self._build_condition(condition)
                        for condition in conditions
                    ]
                    expressions.append(or_(*or_expressions))

                else:
                    expressions.append(self._build_condition(item))

            stmt = stmt.where(and_(*expressions))

        result = await session.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        obj_in: CreateSchemaType,
        *,
        related: dict[str, list] | None = None,
        session: AsyncSession,
    ) -> ModelType:
        """Создает новый объект модели в базе данных.

        Создает новый объект на основе схемы Pydantic,
        фильтрует поля по модели SQLAlchemy, добавляет связанные объекты
        если указано, и сохраняет в базу данных.

        Args:
            obj_in: Pydantic-схема с данными для создания.
            related: опциональные связи many-to-many в формате
                {<relationship_name>: [ORM объекты]}.
            session: асинхронная SQLAlchemy-сессия.

        Returns:
            Созданный объект модели.

        """
        obj_data = obj_in.model_dump()
        model_fields = self._get_model_fields()

        filtered_data = {
            field: value
            for field, value in obj_data.items()
            if field in model_fields
        }

        db_obj = self.model(**filtered_data)

        if related:
            self._apply_relationships(db_obj, related)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        *,
        related: dict[str, list] | None = None,
        session: AsyncSession,
    ) -> ModelType:
        """Обновляет существующий объект модели в базе данных.

        Обновляет только те поля, которые были переданы в Update-схеме.
        Поддерживает обновление связей many-to-many через related.

        Args:
            db_obj: объект, который нужно обновить.
            obj_in: Pydantic-схема с обновляемыми данными.
            related: опциональные связи many-to-many в формате
                {<relationship_name>: [ORM объекты]}.
            session: асинхронная SQLAlchemy-сессия.

        Returns:
            Обновлённый объект модели.

        """
        update_data = obj_in.model_dump(exclude_unset=True)
        model_fields = self._get_model_fields()

        for field, value in update_data.items():
            if value is None:
                continue
            if field in model_fields:
                setattr(db_obj, field, value)

        if related:
            self._apply_relationships(db_obj, related)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def soft_delete(
        self,
        db_obj: ModelType,
        session: AsyncSession,
    ) -> ModelType:
        """Выполняет мягкое удаление объекта.

        Метод не удаляет запись физически из базы данных.
        Вместо этого объект помечается как неактивный путём установки
        флага `active = False`.
        """
        db_obj.active = False
        await session.commit()
        return db_obj

    def _get_model_fields(self) -> set[str]:
        """Возвращает имена всех полей модели."""
        return set(self.model.__mapper__.columns.keys())

    def _apply_relationships(
        self,
        db_obj: ModelType,
        related: dict[str, list],
    ) -> None:
        """Добавляет связанные объекты к экземпляру модели.

        Проверяет, что поля связанных объектов существуют в модели
        и добавляет их к объекту.

        Args:
            db_obj: экземпляр модели, к которому добавляются связи.
            related: опциональные связи many-to-many в формате
                {<relationship_name>: [ORM объекты]}.
            session: асинхронная SQLAlchemy-сессия.

        Raises:
            ValueError: Если указано несуществующее поле связи.

        """
        valid_relationships = self.model.__mapper__.relationships.keys()
        for attr, objs in related.items():
            if attr not in valid_relationships:
                raise ValueError(
                    f'Неизвестное поле "{attr}" '
                    f'для модели "{self.model.__name__}"',
                )
            setattr(db_obj, attr, objs)

    def _build_condition(
        self,
        condition: dict[str, Any],
    ) -> ColumnElement[bool]:
        """Преобразует описание фильтра в SQLAlchemy-условие.

        Проверяет, что поле существует в модели и валидирует операцию.

        Формат condition:
            {
                "field": str,   # имя поля модели
                "op": str,      # операция сравнения
                "value": Any,   # значение для сравнения
            }

        Поддерживаемые операции:
            - eq   : ==
            - like : LIKE
            - gt   : >
            - lt   : <
            - gte  : >=
            - lte  : <=
            - in   : IN

        Args:
            condition: Словарь с описанием фильтра.

        Returns:
            SQLAlchemy Boolean expression.

        Raises:
            ValueError:
            - если поле не существует
            - если операция не поддерживается
            - если value некорректен для операции

        """
        field = condition.get('field')
        op = condition.get('op')
        value = condition.get('value')

        if field not in self._get_model_fields():
            raise ValueError(
                f'Недопустимое поле фильтрации: "{field}".',
            )

        column = getattr(self.model, field)

        if op == 'eq':
            return column == value
        if op == 'like':
            return column.like(value)
        if op == 'gt':
            return column > value
        if op == 'lt':
            return column < value
        if op == 'gte':
            return column >= value
        if op == 'lte':
            return column <= value
        if op == 'in':
            if not isinstance(value, (list, tuple, set)):
                raise ValueError(
                    'Для операции "in" value должен быть итерируемым объектом',
                )
            return column.in_(value)
        raise ValueError(
            f'Неподдерживаемая операция фильтрации: "{op}"',
        )
