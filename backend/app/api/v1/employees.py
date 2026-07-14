"""Employees API skeleton — quản lý nhân viên được giám sát."""

from fastapi import APIRouter

from app.schemas.common import ApiResponse, MessageResponse

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=ApiResponse[MessageResponse])
async def list_employees() -> ApiResponse[MessageResponse]:
    """Danh sách nhân viên — skeleton."""
    return ApiResponse(data=MessageResponse(message="GET /employees — sprint 2"))


@router.get("/{employee_id}", response_model=ApiResponse[MessageResponse])
async def get_employee(employee_id: str) -> ApiResponse[MessageResponse]:
    """Chi tiết nhân viên — skeleton."""
    return ApiResponse(
        data=MessageResponse(message=f"GET /employees/{employee_id} — sprint 2")
    )
