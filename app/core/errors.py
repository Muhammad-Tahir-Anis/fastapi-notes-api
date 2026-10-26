import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def error_response(
    status_code: int,
    message: str,
    details: list[dict] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    error: dict = {"code": status_code, "message": message}
    if details:
        error["details"] = details
    return JSONResponse({"error": error}, status_code=status_code, headers=headers)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(
        "%s %s -> %s %s", request.method, request.url.path, exc.status_code, exc.detail
    )
    return error_response(exc.status_code, str(exc.detail), headers=exc.headers)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [
        {
            "field": ".".join(str(part) for part in err["loc"][1:]),
            "message": err["msg"],
        }
        for err in exc.errors()
    ]
    logger.warning(
        "%s %s -> 422 validation failed (%d errors)",
        request.method,
        request.url.path,
        len(details),
    )
    return error_response(422, "Validation failed", details=details)


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return error_response(500, "Internal server error")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
