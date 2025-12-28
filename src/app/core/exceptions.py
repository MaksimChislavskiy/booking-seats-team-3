import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.error import ErrorResponse


logger = logging.getLogger('cafe_booking')


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Обрабатывает ошибки валидации входных данных."""
    logger.warning(
        'Validation error',
        extra={'user': 'SYSTEM'},
    )

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            code=422,
            message='Validation error',
        ).model_dump(),
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Обрабатывает все HTTPException приложения."""
    logger.warning(
        'HTTP error %s: %s',
        exc.status_code,
        exc.detail,
        extra={'user': 'SYSTEM'},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.status_code,
            message=str(exc.detail),
        ).model_dump(),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Обрабатывает необработанные ошибки сервера (500)."""
    logger.exception(
        'Unhandled server error',
        extra={'user': 'SYSTEM'},
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            code=500,
            message='Internal server error',
        ).model_dump(),
    )
