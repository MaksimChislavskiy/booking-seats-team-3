import logging

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


async def user_not_found_handler(
    request: Request,
    exc: UserNotFoundError,
) -> JSONResponse:
    """Обрабатывает ошибку отсутствия пользователя.

    Вызывается, когда в любом слое приложения выбрасывается
    исключение UserNotFoundError.

    Возвращает HTTP 404 в формате ErrorResponse.
    """
    logger.warning(str(exc))

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            code=status.HTTP_404_NOT_FOUND,
            message=str(exc),
        ).model_dump(),
    )


async def user_already_exists_handler(
    request: Request,
    exc: UserAlreadyExistsError,
) -> JSONResponse:
    """Обрабатывает ошибку конфликта уникальных данных пользователя.

    Используется, когда при создании или обновлении пользователя
    обнаружен конфликт (email, username и т.п.).

    Возвращает HTTP 409 в формате ErrorResponse.
    """
    logger.warning(str(exc))

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ErrorResponse(
            code=status.HTTP_409_CONFLICT,
            message=str(exc),
        ).model_dump(),
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Обрабатывает ошибки валидации данных.

    Переопределяет стандартное поведение FastAPI и возвращает
    унифицированный ответ ErrorResponse вместо дефолтного
    JSON с деталями Pydantic.
    """
    first_error = exc.errors()[0]
    message = first_error.get('msg', 'Ошибка валидации данных')

    logger.warning(message)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ErrorResponse(
            code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            message=message,
        ).model_dump(),
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Обрабатывает все HTTPException, выброшенные в приложении.

    Используется для перехвата ошибок авторизации, прав доступа
    и любых других HTTPException, чтобы вернуть их в формате
    ErrorResponse вместо стандартного ответа FastAPI.
    """
    logger.warning(
        'HTTP %s: %s',
        exc.status_code,
        exc.detail,
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
    """Обрабатывает все необработанные исключения (500).

    Используется как последний уровень защиты приложения.
    """
    logger.exception('Unhandled server error')

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message='Internal server error',
        ).model_dump(),
    )
