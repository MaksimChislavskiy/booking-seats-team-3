import io
from uuid import UUID, uuid4

from PIL import Image
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from app.core.constants import MAX_IMAGE_SIZE, MEDIA_DIR
from app.core.responses import (
    BAD_REQUEST_RESPONSE,
    FORBIDDEN_RESPONSE,
    MEDIA_NOT_FOUND_RESPONSE,
    MEDIA_SAVE_ERROR_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from app.schemas.media import MediaInfo
from app.services.auth import current_admin_or_manager

router = APIRouter()
MEDIA_DIR.mkdir(exist_ok=True)


@router.post(
    '',
    response_model=MediaInfo,
    status_code=status.HTTP_200_OK,
    summary='Загрузка изображения',
    description=(
        'Загружает JPG или PNG (макс 5 МБ), '
        'конвертирует в JPG и возвращает UUID. '
        'Доступно только администраторам и менеджерам.'
    ),
    dependencies=[Depends(current_admin_or_manager)],
    responses={
        200: {
            'description': 'Успешно',
            'model': MediaInfo,
        },
        **BAD_REQUEST_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **MEDIA_SAVE_ERROR_RESPONSE,
    },
)
async def upload_image(
    file: UploadFile = File(
        ...,
        description='Загружаемый файл',
    ),
) -> MediaInfo:
    """Загрузка изображения (только JPG/PNG, max 5 МБ)."""
    if file.content_type not in ('image/jpeg', 'image/png'):
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
    img.save(MEDIA_DIR / f'{image_id}.jpg', 'JPEG', quality=95)

    return MediaInfo(media_id=image_id)


@router.get(
    '/{media_id}',
    summary='Возвращает изображение в бинарном формате',
    responses={
        200: {
            'description': (
                'Успешно. Возвращает изображение '
                'в бинарном формате'
),

            'content': {
                'image/jpeg': {},
            },
        },
        **MEDIA_NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def get_image(
    media_id: UUID = Path(
        ...,
        title='Media ID',
        description='ID изображения',
    ),
) -> FileResponse:
    file_path = MEDIA_DIR / f'{media_id}.jpg'
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Изображение не найдено',
        )

    return FileResponse(file_path, media_type='image/jpeg')
