"""
Đăng ký exception handlers cho FastAPI.

Chuyển AEMSException → JSON response chuẩn hóa.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.exceptions.base import AEMSException


def register_exception_handlers(app: FastAPI) -> None:
    """
    Gắn handler xử lý exception tùy chỉnh lên FastAPI app.

    Args:
        app: Instance FastAPI cần đăng ký handler.
    """

    @app.exception_handler(AEMSException)
    async def aems_exception_handler(
        request: Request, exc: AEMSException
    ) -> JSONResponse:
        """Map AEMSException sang HTTP status code phù hợp."""
        status_map = {
            "NOT_FOUND": 404,
            "UNAUTHORIZED": 401,
            "FORBIDDEN": 403,
            "VALIDATION_ERROR": 422,
            "CONFLICT": 409,
            "CAMERA_NOT_RUNNING": 409,
            "FRAME_BUFFER_EMPTY": 404,
            "RTSP_CONNECTION_ERROR": 503,
        }
        status_code = status_map.get(exc.code, 400)
        logger.warning(
            "AEMSException | path={} code={} msg={}",
            request.url.path,
            exc.code,
            exc.message,
        )
        return JSONResponse(
            status_code=status_code,
            content={
                "data": None,
                "error": {"code": exc.code, "message": exc.message},
            },
        )
