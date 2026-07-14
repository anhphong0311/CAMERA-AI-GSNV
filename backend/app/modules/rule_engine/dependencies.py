"""
Dependency Injection + lifecycle cho Rule Engine module.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request
from loguru import logger

from app.modules.rule_engine.services import RuleService

_service: Optional[RuleService] = None


async def init_rule_engine_module(app) -> RuleService:
    """
    Khởi tạo Rule Engine khi app startup.

    - Tạo RuleService (load rule_engine.yaml, cooldown.yaml).
    - Seed rules từ rules.yaml.
    """
    global _service
    service = RuleService()
    count = service.load_rules_file()
    _service = service
    app.state.rule_service = service
    logger.info("Rule Engine module initialized ({} rules loaded)", count)
    return service


async def shutdown_rule_engine_module() -> None:
    """Dọn dẹp khi shutdown."""
    global _service
    if _service is not None:
        _service.shutdown()
    _service = None
    logger.info("Rule Engine module shutdown complete")


def get_rule_service(request: Request) -> RuleService:
    """FastAPI dependency — RuleService từ app.state."""
    service: Optional[RuleService] = getattr(
        request.app.state, "rule_service", None
    )
    if service is None:
        raise RuntimeError("RuleService chưa được khởi tạo.")
    return service
