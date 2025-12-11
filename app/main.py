from fastapi import FastAPI

from app.api.routers import main_router
from app.core.config import settings
from app.core.logging import setup_logging

logger = setup_logging()
logger.info("Cafe Booking API starting...")

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
)

app.include_router(main_router)
