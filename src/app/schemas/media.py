from uuid import UUID

from pydantic import BaseModel, Field


class MediaUploadResponse(BaseModel):
    """Ответ после успешной загрузки изображения."""

    media_id: UUID = Field(
        ...,
        description="UUID загруженного изображения",
        example="123e4567-e89b-12d3-a456-426614174000",
    )
