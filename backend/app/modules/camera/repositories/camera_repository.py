"""
CameraRepository — truy cập bảng cameras (Repository Pattern).
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictError, NotFoundError
from app.models.camera import Camera
from app.modules.camera.schemas.camera import CameraCreate, CameraUpdate
from app.repositories.base import BaseRepository


class CameraRepository(BaseRepository[Camera]):
    """
    Repository CRUD cho entity Camera.

    Kế thừa BaseRepository — mở rộng query đặc thù camera.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Camera, session)

    async def get_by_code(self, code: str) -> Optional[Camera]:
        """Tìm camera theo mã code."""
        stmt = select(Camera).where(Camera.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Camera]:
        """Danh sách camera có phân trang."""
        stmt = select(Camera).order_by(Camera.id).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_enabled(self) -> List[Camera]:
        """Camera enabled=true — dùng auto-start khi app boot."""
        stmt = select(Camera).where(Camera.enabled.is_(True)).order_by(Camera.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: CameraCreate) -> Camera:
        """
        Tạo camera mới.

        Raises:
            ConflictError: Trùng code.
        """
        existing = await self.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Camera code '{data.code}' đã tồn tại.")
        camera = Camera(
            code=data.code,
            name=data.name,
            location=data.location,
            rtsp_main=data.rtsp_main,
            rtsp_sub=data.rtsp_sub,
            department_id=data.department_id,
            resolution=data.resolution,
            fps=data.fps,
            enabled=data.enabled,
            status="offline",
        )
        return await self.add(camera)

    async def update(self, camera_id: int, data: CameraUpdate) -> Camera:
        """
        Cập nhật camera.

        Raises:
            NotFoundError: Không tìm thấy camera.
            ConflictError: Trùng code khi đổi code.
        """
        camera = await self.get_by_id(camera_id)
        if camera is None:
            raise NotFoundError("Camera", camera_id)

        payload = data.model_dump(exclude_unset=True)
        if "code" in payload and payload["code"] != camera.code:
            dup = await self.get_by_code(payload["code"])
            if dup:
                raise ConflictError(f"Camera code '{payload['code']}' đã tồn tại.")

        for key, value in payload.items():
            setattr(camera, key, value)
        await self.session.flush()
        await self.session.refresh(camera)
        return camera

    async def delete(self, camera_id: int) -> None:
        """Xóa camera."""
        camera = await self.get_by_id(camera_id)
        if camera is None:
            raise NotFoundError("Camera", camera_id)
        await super().delete(camera)

    async def update_heartbeat(
        self,
        camera_id: int,
        status: str,
        *,
        set_online: bool = False,
    ) -> None:
        """
        Cập nhật heartbeat và status từ worker.

        Args:
            camera_id: ID camera.
            status: online | offline | reconnecting | lagging.
            set_online: True thì cập nhật last_online.
        """
        camera = await self.get_by_id(camera_id)
        if camera is None:
            return
        now = datetime.now(timezone.utc)
        camera.status = status
        camera.last_heartbeat = now
        if set_online:
            camera.last_online = now
        await self.session.flush()

    @staticmethod
    def resolve_rtsp_url(camera: Camera) -> str:
        """URL stream ưu tiên sub → main."""
        return camera.rtsp_sub or camera.rtsp_main
