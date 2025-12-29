from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CafeShortInfo(BaseModel):
    """Сокращённая информация о кафе."""

    id: int = Field(
        ...,
        title='Идентификатор кафе',
        description='Уникальный идентификатор кафе.',
    )
    name: str = Field(
        ...,
        title='Название кафе',
        description='Отображаемое название кафе.',
    )
    address: str = Field(
        ...,
        title='Адрес кафе',
        description='Физический адрес расположения кафе.',
    )
    phone: str = Field(
        ...,
        title='Контактный телефон',
        description='Основной контактный номер телефона кафе.',
    )
    description: str | None = Field(
        None,
        title='Описание кафе',
        description='Краткое описание или дополнительная информация о кафе.',
    )
    photo_id: UUID | None = Field(
        None,
        title='Идентификатор фотографии',
        description='UUID фотографии, связанной с кафе.',
    )

    model_config = ConfigDict(
        from_attributes=True,
    )
