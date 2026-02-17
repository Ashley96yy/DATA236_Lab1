from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _build_error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


def _http_status_to_code(status_code: int) -> str:
    status_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
    }
    return status_map.get(status_code, f"HTTP_{status_code}")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def handle_starlette_http_exception(
        _: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = _http_status_to_code(exc.status_code)
        message = str(exc.detail) if exc.detail else "Request failed."
        return _build_error_response(exc.status_code, code, message)

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        code = _http_status_to_code(exc.status_code)
        message = str(exc.detail) if exc.detail else "Request failed."
        return _build_error_response(exc.status_code, code, message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else None
        message = "Invalid request."
        if first_error is not None:
            message = str(first_error.get("msg", message))
        return _build_error_response(422, "VALIDATION_ERROR", message)

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_: Request, __: Exception) -> JSONResponse:
        return _build_error_response(500, "INTERNAL_SERVER_ERROR", "Internal server error.")
