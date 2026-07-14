"""
Exception hierarchy tùy chỉnh cho AEMS.

Tách exception khỏi FastAPI/HTTP layer để service layer
có thể raise lỗi domain mà không phụ thuộc framework.
"""


class AEMSException(Exception):
    """
    Lớp cơ sở cho mọi exception nghiệp vụ/kỹ thuật của AEMS.

    Attributes:
        message: Thông báo lỗi hiển thị cho client.
        code: Mã lỗi machine-readable (dùng trong API response).
    """

    def __init__(self, message: str, code: str = "AEMS_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(AEMSException):
    """Entity không tồn tại trong database."""

    def __init__(self, entity: str, entity_id: str | int) -> None:
        super().__init__(
            message=f"{entity} với id={entity_id} không tồn tại.",
            code="NOT_FOUND",
        )


class UnauthorizedError(AEMSException):
    """Xác thực thất bại hoặc token không hợp lệ."""

    def __init__(self, message: str = "Không được phép truy cập.") -> None:
        super().__init__(message=message, code="UNAUTHORIZED")


class ForbiddenError(AEMSException):
    """Đã xác thực nhưng không đủ quyền (RBAC)."""

    def __init__(self, message: str = "Không đủ quyền thực hiện thao tác.") -> None:
        super().__init__(message=message, code="FORBIDDEN")


class ValidationError(AEMSException):
    """Dữ liệu đầu vào không hợp lệ ở tầng service."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR")


class ConflictError(AEMSException):
    """Xung đột dữ liệu (duplicate key, trạng thái không hợp lệ)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="CONFLICT")
