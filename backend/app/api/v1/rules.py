"""
Rules API — Sprint 6 (AI Rule Engine).

Endpoints (mount dưới /api/v1):
- GET    /rules                  → danh sách rule
- POST   /rules                  → tạo rule (JSON/YAML đã parse)
- GET    /rules/statistics       → thống kê engine
- GET    /rules/performance      → điểm hiệu suất (tất cả track)
- GET    /rules/flow             → visualization pipeline
- GET    /rules/lifecycle        → visualization vòng đời event
- POST   /rules/enable           → bật rule
- POST   /rules/disable          → tắt rule
- GET    /rules/{rule_id}        → chi tiết rule (+ condition tree)
- PUT    /rules/{rule_id}        → cập nhật rule
- DELETE /rules/{rule_id}        → xóa rule

KHÔNG Telegram / Database / Dashboard.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.exceptions.base import NotFoundError
from app.modules.rule_engine.dependencies import get_rule_service
from app.modules.rule_engine.exceptions import RuleNotFoundError
from app.modules.rule_engine.schemas import (
    RuleCreateRequest,
    RuleToggleRequest,
    RuleUpdateRequest,
    to_rule_dict,
)
from app.modules.rule_engine.services import RuleService
from app.modules.rule_engine.visualization import (
    condition_tree,
    event_lifecycle,
    rule_flow,
)
from app.schemas.common import ApiResponse, MessageResponse

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.get("", response_model=ApiResponse[list])
async def list_rules(
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[list]:
    """Danh sách tất cả rule."""
    return ApiResponse(data=[r.to_dict() for r in service.list_rules()])


@router.post("", response_model=ApiResponse[dict])
async def create_rule(
    body: RuleCreateRequest,
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[dict]:
    """Tạo rule mới."""
    rule = service.add_rule(to_rule_dict(body))
    return ApiResponse(data=rule.to_dict())


@router.get("/statistics", response_model=ApiResponse[dict])
async def get_statistics(
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[dict]:
    """Thống kê Rule Engine."""
    return ApiResponse(data=service.statistics())


@router.get("/performance", response_model=ApiResponse[list])
async def get_performance(
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[list]:
    """Điểm hiệu suất của tất cả track."""
    return ApiResponse(data=service.performance_reports())


@router.get("/flow", response_model=ApiResponse[dict])
async def get_flow() -> ApiResponse[dict]:
    """Sơ đồ pipeline Rule Engine."""
    return ApiResponse(data=rule_flow())


@router.get("/lifecycle", response_model=ApiResponse[dict])
async def get_lifecycle() -> ApiResponse[dict]:
    """Sơ đồ vòng đời event."""
    return ApiResponse(data=event_lifecycle())


@router.post("/enable", response_model=ApiResponse[dict])
async def enable_rule(
    body: RuleToggleRequest,
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[dict]:
    """Bật rule."""
    try:
        rule = service.set_enabled(body.rule_id, True)
    except RuleNotFoundError as exc:
        raise NotFoundError("Rule", body.rule_id) from exc
    return ApiResponse(data=rule.to_dict())


@router.post("/disable", response_model=ApiResponse[dict])
async def disable_rule(
    body: RuleToggleRequest,
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[dict]:
    """Tắt rule."""
    try:
        rule = service.set_enabled(body.rule_id, False)
    except RuleNotFoundError as exc:
        raise NotFoundError("Rule", body.rule_id) from exc
    return ApiResponse(data=rule.to_dict())


@router.get("/{rule_id}", response_model=ApiResponse[dict])
async def get_rule(
    rule_id: str,
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[dict]:
    """Chi tiết rule + condition tree."""
    try:
        rule = service.get_rule(rule_id)
    except RuleNotFoundError as exc:
        raise NotFoundError("Rule", rule_id) from exc
    data = rule.to_dict()
    data["visualization"] = condition_tree(rule)
    return ApiResponse(data=data)


@router.put("/{rule_id}", response_model=ApiResponse[dict])
async def update_rule(
    rule_id: str,
    body: RuleUpdateRequest,
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[dict]:
    """Cập nhật rule."""
    try:
        rule = service.update_rule(rule_id, to_rule_dict(body))
    except RuleNotFoundError as exc:
        raise NotFoundError("Rule", rule_id) from exc
    return ApiResponse(data=rule.to_dict())


@router.delete("/{rule_id}", response_model=ApiResponse[MessageResponse])
async def delete_rule(
    rule_id: str,
    service: RuleService = Depends(get_rule_service),
) -> ApiResponse[MessageResponse]:
    """Xóa rule."""
    try:
        service.delete_rule(rule_id)
    except RuleNotFoundError as exc:
        raise NotFoundError("Rule", rule_id) from exc
    return ApiResponse(data=MessageResponse(message=f"Đã xóa rule {rule_id}"))
