"""오류를 RFC 9457 problem+json 으로 통일한다."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .logging import request_id_var


class AppError(Exception):
    def __init__(self, code: str, status: int, detail: str):
        self.code = code
        self.status = status
        self.detail = detail
        super().__init__(detail)


def _problem(status: int, title: str, detail: str, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"about:blank#{code}",
            "title": title,
            "status": status,
            "detail": detail,
            "request_id": request_id_var.get(),
        },
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return _problem(exc.status, exc.code, exc.detail, exc.code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        return _problem(422, "validation_error", str(exc.errors()), "validation_error")

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception):
        return _problem(500, "internal_error", "예기치 못한 오류가 발생했습니다.", "internal_error")
