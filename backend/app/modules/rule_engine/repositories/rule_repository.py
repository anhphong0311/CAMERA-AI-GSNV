"""
RuleRepository — kho Rule in-memory (CRUD), seed từ rules.yaml.

KHÔNG dùng Database (Sprint 6 cấm persistence).
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from app.modules.rule_engine.exceptions import DuplicateRuleError, RuleNotFoundError
from app.modules.rule_engine.rule_parser.rule import Rule


class RuleRepository:
    """Lưu trữ Rule trong bộ nhớ."""

    def __init__(self) -> None:
        self._rules: Dict[str, Rule] = {}
        self._lock = threading.RLock()

    def add(self, rule: Rule) -> Rule:
        """Thêm rule mới (raise nếu trùng id)."""
        with self._lock:
            if rule.id in self._rules:
                raise DuplicateRuleError(rule.id)
            self._rules[rule.id] = rule
            return rule

    def upsert(self, rule: Rule) -> Rule:
        """Thêm/ghi đè rule."""
        with self._lock:
            self._rules[rule.id] = rule
            return rule

    def update(self, rule: Rule) -> Rule:
        """Cập nhật rule tồn tại (raise nếu không có)."""
        with self._lock:
            if rule.id not in self._rules:
                raise RuleNotFoundError(rule.id)
            self._rules[rule.id] = rule
            return rule

    def get(self, rule_id: str) -> Optional[Rule]:
        """Lấy rule theo id."""
        with self._lock:
            return self._rules.get(rule_id)

    def require(self, rule_id: str) -> Rule:
        """Lấy rule hoặc raise."""
        rule = self.get(rule_id)
        if rule is None:
            raise RuleNotFoundError(rule_id)
        return rule

    def delete(self, rule_id: str) -> None:
        """Xóa rule."""
        with self._lock:
            if rule_id not in self._rules:
                raise RuleNotFoundError(rule_id)
            del self._rules[rule_id]

    def set_enabled(self, rule_id: str, enabled: bool) -> Rule:
        """Bật/tắt rule."""
        rule = self.require(rule_id)
        rule.enabled = enabled
        return rule

    def list(self) -> List[Rule]:
        """Danh sách tất cả rule."""
        with self._lock:
            return list(self._rules.values())

    def enabled_rules(self) -> List[Rule]:
        """Rule đang bật, sắp theo priority tăng dần."""
        with self._lock:
            return sorted(
                (r for r in self._rules.values() if r.enabled),
                key=lambda r: r.priority,
            )

    def clear(self) -> None:
        with self._lock:
            self._rules.clear()
