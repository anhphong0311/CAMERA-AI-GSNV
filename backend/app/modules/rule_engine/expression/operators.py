"""
Operators — bảng toán tử so sánh cho expression engine.

An toàn: không dùng eval(). Chỉ map operator chuỗi → hàm thuần.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from app.modules.rule_engine.exceptions import ExpressionError


def _num(a: Any, b: Any) -> tuple[float, float]:
    """Ép về số để so sánh; raise nếu không hợp lệ."""
    try:
        return float(a), float(b)
    except (TypeError, ValueError) as exc:
        raise ExpressionError(f"Không thể so sánh số: {a!r} vs {b!r}") from exc


def _eq(a: Any, b: Any) -> bool:
    return a == b


def _ne(a: Any, b: Any) -> bool:
    return a != b


def _gt(a: Any, b: Any) -> bool:
    if a is None:
        return False
    x, y = _num(a, b)
    return x > y


def _ge(a: Any, b: Any) -> bool:
    if a is None:
        return False
    x, y = _num(a, b)
    return x >= y


def _lt(a: Any, b: Any) -> bool:
    if a is None:
        return False
    x, y = _num(a, b)
    return x < y


def _le(a: Any, b: Any) -> bool:
    if a is None:
        return False
    x, y = _num(a, b)
    return x <= y


def _in(a: Any, b: Any) -> bool:
    try:
        return a in b
    except TypeError as exc:
        raise ExpressionError(f"Toán tử 'in' không áp dụng: {a!r} in {b!r}") from exc


def _not_in(a: Any, b: Any) -> bool:
    return not _in(a, b)


def _contains(a: Any, b: Any) -> bool:
    try:
        return b in a
    except TypeError as exc:
        raise ExpressionError(f"Toán tử 'contains' không áp dụng: {a!r}") from exc


OPERATORS: Dict[str, Callable[[Any, Any], bool]] = {
    "==": _eq,
    "!=": _ne,
    ">": _gt,
    ">=": _ge,
    "<": _lt,
    "<=": _le,
    "in": _in,
    "not_in": _not_in,
    "contains": _contains,
}


def evaluate_operator(operator: str, left: Any, right: Any) -> bool:
    """
    Áp dụng operator lên (left, right).

    Args:
        operator: Ký hiệu toán tử.
        left: Giá trị fact.
        right: Giá trị so sánh trong rule.

    Returns:
        bool kết quả.

    Raises:
        ExpressionError: Operator không hỗ trợ.
    """
    fn = OPERATORS.get(operator)
    if fn is None:
        raise ExpressionError(f"Toán tử không hỗ trợ: {operator}")
    return fn(left, right)
