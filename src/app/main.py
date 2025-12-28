from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routers import main_router
from app.core.config import settings
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.core.openapi import OPENAPI_TAGS

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan-обработчик запуска и остановки приложения."""
    logger.info('Cafe Booking API starting...')
    yield
    logger.info('Cafe Booking API shutting down...')


app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
)

app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)
app.add_exception_handler(
    Exception,
    unhandled_exception_handler,
)

app.include_router(main_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['OPTIONS', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
    allow_headers=['Authorization', 'Content-Type'],
)
