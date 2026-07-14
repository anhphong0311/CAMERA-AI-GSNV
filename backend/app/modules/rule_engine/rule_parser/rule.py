"""
Rule — domain model của một quy tắc (config-driven).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from app.modules.rule_engine.condition.nodes import ConditionNode
from app.modules.rule_engine.event.severity import Severity

# Map rule_id → nhóm hành vi (phục vụ Performance Score)
CATEGORY_MAP = {
    "PHONE_USAGE": "phone",
    "AWAY_FROM_DESK": "away",
    "PRIVATE_TALKING": "talking",
    "EATING": "eating",
    "SLEEPING": "sleeping",
    "IDLE": "idle",
}


@dataclass
class Rule:
    """
    Quy tắc suy luận hành vi.

    Attributes:
        id: Mã rule (duy nhất).
        name: Tên hiển thị.
        enabled: Bật/tắt.
        severity: Mức nghiêm trọng khi kích hoạt.
        priority: Độ ưu tiên (số nhỏ = ưu tiên cao).
        cooldown: Cooldown riêng (giây); None → dùng cấu hình chung.
        actions: Danh sách hành động (vd ["alert"]).
        condition: Cây điều kiện.
        description: Mô tả.
        category: Nhóm hành vi (tính điểm); mặc định suy từ id.
    """

    id: str
    name: str
    condition: ConditionNode
    enabled: bool = True
    severity: Severity = Severity.INFO
    priority: int = 3
    cooldown: Optional[float] = None
    actions: List[str] = field(default_factory=lambda: ["alert"])
    description: str = ""
    category: Optional[str] = None

    def __post_init__(self) -> None:
        if self.category is None:
            self.category = CATEGORY_MAP.get(self.id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize rule (API + reload)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "severity": self.severity.value,
            "priority": self.priority,
            "cooldown": self.cooldown,
            "actions": list(self.actions),
            "category": self.category,
            "conditions": self.condition.to_dict(),
        }
