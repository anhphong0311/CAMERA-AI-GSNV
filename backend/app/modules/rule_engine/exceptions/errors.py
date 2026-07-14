"""
Exception hierarchy cho Rule Engine.
"""

from app.exceptions.base import AEMSException


class RuleEngineException(AEMSException):
    """Lớp cơ sở cho lỗi Rule Engine."""

    def __init__(self, message: str, code: str = "RULE_ENGINE_ERROR") -> None:
        super().__init__(message=message, code=code)


class InvalidRuleError(RuleEngineException):
    """Rule không hợp lệ (thiếu field, sai cấu trúc)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="INVALID_RULE")


class CircularRuleError(RuleEngineException):
    """Cấu trúc điều kiện lồng nhau vượt giới hạn / vòng lặp."""

    def __init__(self, message: str = "Điều kiện lồng nhau quá sâu / vòng lặp.") -> None:
        super().__init__(message=message, code="CIRCULAR_RULE")


class MissingParameterError(RuleEngineException):
    """Thiếu tham số bắt buộc trong điều kiện."""

    def __init__(self, parameter: str) -> None:
        super().__init__(message=f"Thiếu tham số: {parameter}", code="MISSING_PARAMETER")


class ExpressionError(RuleEngineException):
    """Lỗi khi đánh giá biểu thức/operator."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="EXPRESSION_ERROR")


class RuleTimeoutError(RuleEngineException):
    """Rule thực thi quá thời gian cho phép."""

    def __init__(self, rule_id: str) -> None:
        super().__init__(message=f"Rule timeout: {rule_id}", code="RULE_TIMEOUT")


class DuplicateRuleError(RuleEngineException):
    """Trùng ID rule khi thêm mới."""

    def __init__(self, rule_id: str) -> None:
        super().__init__(message=f"Rule đã tồn tại: {rule_id}", code="DUPLICATE_RULE")


class RuleNotFoundError(RuleEngineException):
    """Không tìm thấy rule."""

    def __init__(self, rule_id: str) -> None:
        super().__init__(message=f"Không tìm thấy rule: {rule_id}", code="RULE_NOT_FOUND")
