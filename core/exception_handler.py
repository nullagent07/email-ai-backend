import logging

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from app.presentation.schemas.problem import ProblemDetail
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("email-assistant")


async def custom_validation_exception_handler(
    request: Request,  # noqa: ARG001
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle custom validation exceptions.

    Args:
    ----
        request (Request): The request object.
        exc (RequestValidationError): The validation exception.

    Returns:
    -------
        JSONResponse: The JSON response.

    """
    logger.error(exc.errors())
    problem_detail = ProblemDetail(
        type="validation_error",
        title="Ошибка валидации данных",
        text="Проверьте введенные данные на корректность.",
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=exc.errors(),
    )
    return JSONResponse(
        content=problem_detail.model_dump(exclude_none=True),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


# Общий обработчик для HTTPException
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:  # noqa: ARG001
    """Handle HTTP exceptions and return a JSON response.

    Args:
    ----
        request (Request): The request object.
        exc (HTTPException): The HTTP exception.

    Returns:
    -------
        JSONResponse: The JSON response.

    """
    logger.error(exc.detail)
    problem_detail = ProblemDetail(
        type="internal_server_error",
        status=exc.status_code,
        title="Внутренняя ошибка сервера",
        text=exc.detail or "Произошла ошибка при обработке запроса.",
        detail=[],
    )

    match exc.status_code:
        case status.HTTP_401_UNAUTHORIZED:
            problem_detail = ProblemDetail(
                type="unauthorized",
                title="Ошибка авторизации",
                text=exc.detail or "Пользователь не авторизован.",
                status=exc.status_code,
                detail=[],
            )
        case status.HTTP_403_FORBIDDEN:
            problem_detail = ProblemDetail(
                type="forbidden",
                title="Ошибка доступа",
                text=exc.detail or "Пользователь не имеет прав.",
                status=exc.status_code,
                detail=[],
            )
        case status.HTTP_404_NOT_FOUND:
            problem_detail = ProblemDetail(
                type="not_found",
                title="Ресурс не найден",
                text=exc.detail or "Запрашиваемый ресурс не найден.",
                status=exc.status_code,
                detail=[],
            )
        case status.HTTP_405_METHOD_NOT_ALLOWED:
            problem_detail = ProblemDetail(
                type="method_not_allowed",
                title="Метод не разрешен",
                text=exc.detail or "Метод не разрешен для данного ресурса.",
                status=exc.status_code,
                detail=[],
            )
        case status.HTTP_422_UNPROCESSABLE_ENTITY:
            problem_detail = ProblemDetail(
                type="validation_error",
                title="Ошибка валидации данных",
                text=exc.detail or "Проверьте введенные данные на корректность.",
                status=exc.status_code,
                detail=[],
            )
        case status.HTTP_500_INTERNAL_SERVER_ERROR:
            problem_detail = ProblemDetail(
                type="internal_server_error",
                title="Внутренняя ошибка сервера",
                text=exc.detail or "Произошла неожиданная ошибка.",
                status=exc.status_code,
                detail=[],
            )

    return JSONResponse(
        content=problem_detail.model_dump(exclude_none=True),
        status_code=exc.status_code,
    )


# Обработчик для остальных необработанных исключений
async def all_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    """Handle all unhandled exceptions and return a JSON response.

    Args:
    ----
        request (Request): The request object.
        exc (Exception): The unhandled exception.

    Returns:
    -------
        JSONResponse: The JSON response.

    """
    logger.error(exc)
    problem_detail = ProblemDetail(
        type="internal_server_error",
        title="Внутренняя ошибка сервера",
        text="Произошла неожиданная ошибка.",
        status=500,
        detail=[],
    )
    return JSONResponse(
        content=problem_detail.model_dump(exclude_none=True),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def starlette_http_exception_handler(
    request: Request,  # noqa: ARG001
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle Starlette HTTP exceptions and return a JSON response."""
    logger.error(exc.detail)
    problem_detail = ProblemDetail(
        type="internal_server_error",
        status=exc.status_code,
        title="Внутренняя ошибка сервера",
        text=exc.detail or "Произошла ошибка при обработке запроса.",
        detail=[],
    )

    match exc.status_code:
        case status.HTTP_403_FORBIDDEN:
            problem_detail = ProblemDetail(
                type="forbidden",
                title="Ошибка доступа",
                text=exc.detail or "Пользователь не имеет прав.",
                status=exc.status_code,
                detail=[],
            )
        case status.HTTP_404_NOT_FOUND:
            problem_detail = ProblemDetail(
                type="not_found",
                title="Ресурс не найден",
                text=exc.detail or "Запрашиваемый ресурс не найден.",
                status=exc.status_code,
                detail=[],
            )
        case status.HTTP_405_METHOD_NOT_ALLOWED:
            problem_detail = ProblemDetail(
                type="method_not_allowed",
                title="Метод не разрешен",
                text=exc.detail or "Метод не разрешен для данного ресурса.",
                status=exc.status_code,
                detail=[],
            )
        case status.HTTP_400_BAD_REQUEST:
            problem_detail = ProblemDetail(
                type="bad_request",
                title="Неверный запрос",
                text=exc.detail or "Запрос не может быть обработан.",
                status=exc.status_code,
                detail=[],
            )
        case status.HTTP_500_INTERNAL_SERVER_ERROR:
            problem_detail = ProblemDetail(
                type="internal_server_error",
                title="Внутренняя ошибка сервера",
                text=exc.detail or "Произошла неожиданная ошибка.",
                status=exc.status_code,
                detail=[],
            )

    return JSONResponse(
        content=problem_detail.model_dump(exclude_none=True),
        status_code=exc.status_code,
    )