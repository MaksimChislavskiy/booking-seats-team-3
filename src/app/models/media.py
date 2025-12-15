from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import (
    MAX_LENGTH_MEDIA_CONTENTTYPE,
    MAX_LENGTH_MEDIA_FILENAME,
    MAX_LENGTH_MEDIA_FILEPATH,
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
    file_name: Mapped[str] = mapped_column(
        String(MAX_LENGTH_MEDIA_FILENAME),
        nullable=False,
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
    content_type: Mapped[str] = mapped_column(
        String(MAX_LENGTH_MEDIA_CONTENTTYPE),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f'<Media id={self.id}, '
            f'file_name={self.file_name}, '
            f'size={self.size}, '
            f'content_type={self.content_type}>'
        )

    def __str__(self) -> str:
        return f'{self.file_name}: {self.file_path}'
