import io
from pathlib import Path
from uuid import uuid4

from PIL import Image
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

router = APIRouter(tags=["Медиа"])

MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(exist_ok=True)

MAX_SIZE = 5 * 1024 * 1024  # 5 МБ


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Загрузка изображения (только JPG/PNG, max 5 МБ)."""
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только JPG и PNG",
        )

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл слишком большой (максимум 5 МБ)",
        )

    try:
        img = Image.open(io.BytesIO(content))
        img = img.convert("RGB")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно обработать изображение",
        )

    image_id = uuid4()
    file_path = MEDIA_DIR / f"{image_id}.jpg"
    img.save(file_path, "JPEG", quality=95)

    return {"id": str(image_id)}


@router.get("/{image_id}")
async def get_image(image_id: str):
    """Отдача изображения по ID."""
    file_path = MEDIA_DIR / f"{image_id}.jpg"
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Изображение не найдено",
        )

    return FileResponse(file_path, media_type="image/jpeg")
