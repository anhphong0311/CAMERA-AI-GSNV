"""
Severity — mức độ nghiêm trọng của Event (enum + rank).
"""

from __future__ import annotations

from enum import Enum


class Severity(str, Enum):
    """Mức độ nghiêm trọng."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    @property
    def rank(self) -> int:
        """Rank số (cao = nghiêm trọng hơn)."""
        return {
            "CRITICAL": 5,
            "HIGH": 4,
            "MEDIUM": 3,
            "LOW": 2,
            "INFO": 1,
        }[self.value]

    @classmethod
    def from_str(cls, value: str) -> "Severity":
        """Parse severity từ chuỗi (mặc định INFO)."""
        try:
            return cls(value.upper())
        except (ValueError, AttributeError):
            return cls.INFO
