from uuid import UUID, uuid4

from sqlalchemy import Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import (
    MAX_LENGTH_MEDIA_FILEPATH,
    MEDIA_PATH_DISPLAY_LENGTH,
)
from app.core.db import Base


class Media(Base):
    """Модель для хранения метаданных загруженных фотографий.

    Модель не содержит бинарные данные файла.
    Файлы хранятся во внешнем хранилище, а Media используется для:
    - идентификации файла,
    - хранения пути к файлу,
    - хранения технических характеристик,
    - связывания с доменными сущностями.
    """

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    active: Mapped[bool | None] = mapped_column(
        nullable=True,
        default=None,
        server_default=text('null'),
    )
    file_path: Mapped[str] = mapped_column(
        String(MAX_LENGTH_MEDIA_FILEPATH),
        nullable=False,
        unique=True,
    )
    size: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f'<Media id={self.id}, '
            f'file_path={self.file_path[-MEDIA_PATH_DISPLAY_LENGTH:]}, '
            f'size={self.size}>'
        )

    def __str__(self) -> str:
        return f'...{self.file_path[-MEDIA_PATH_DISPLAY_LENGTH:]}'
