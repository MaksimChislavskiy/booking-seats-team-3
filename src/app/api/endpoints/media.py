import io
from pathlib import Path
from uuid import uuid4

from PIL import Image
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.responses import (
    NOT_FOUND_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)

from src.app.core.constants import MAX_IMAGE_SIZE, MEDIA_DIR_PATH
from src.app.schemas.media import MediaUploadResponse

router = APIRouter()

MEDIA_DIR = Path(MEDIA_DIR_PATH)
MEDIA_DIR.mkdir(exist_ok=True)


@router.post(
    '/',
    response_model=MediaUploadResponse,
    summary='Загрузка изображения',
    description=(
        'Загружает JPG или PNG (макс 5 МБ), '
        'конвертирует в JPG и возвращает UUID'
    ),
)
async def upload_image(file: UploadFile = File(...)) -> MediaUploadResponse:
    """Загрузка изображения (только JPG/PNG, max 5 МБ)."""
    if file.content_type not in ['image/jpeg', 'image/png']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Поддерживаются только JPG и PNG',
        )

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Файл слишком большой (максимум 5 МБ)',
        )

    try:
        img = Image.open(io.BytesIO(content))
        img = img.convert('RGB')
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Невозможно обработать изображение',
        )

    image_id = uuid4()
    file_path = MEDIA_DIR / f'{image_id}.jpg'
    img.save(file_path, 'JPEG', quality=95)

    return MediaUploadResponse(media_id=image_id)


@router.get(
    '/{media_id}',
    summary='Получение изображения',
    description='Возвращает изображение по UUID',
    responses={
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def get_image(media_id: str) -> FileResponse:
    """Отдача изображения по ID."""
    file_path = MEDIA_DIR / f'{media_id}.jpg'
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Изображение не найдено',
        )

    return FileResponse(file_path, media_type='image/jpeg')
