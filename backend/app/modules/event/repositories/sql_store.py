"""
SqlEventStore — persistence EventRecord vào PostgreSQL (async).

Dùng khi event.yaml `persist_db: true`. Mặc định pipeline dùng InMemoryEventStore;
SqlEventStore được gọi bổ sung ở tầng async của EventService.
"""

from __future__ import annotations

from typing import List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.models.event_processing import (
    EventNotificationORM,
    EventRecordORM,
    EventRetryORM,
)
from app.modules.event.schemas.records import EventRecord


class SqlEventStore:
    """Kho EventRecord trên Database (async)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def persist(self, record: EventRecord) -> None:
        """Upsert một EventRecord + notifications + retries."""
        try:
            async with self._factory() as session:
                orm = await self._get(session, record.event_id)
                if orm is None:
                    orm = EventRecordORM(event_id=record.event_id)
                    session.add(orm)
                self._apply(orm, record)
                await session.flush()
                # ghi lại notifications (đơn giản: xóa + tạo lại)
                orm.notifications.clear()
                for n in record.notifications:
                    n_orm = EventNotificationORM(
                        channel=n.channel,
                        target=n.target,
                        status=n.status.value,
                        attempts=n.attempts,
                        error=n.error,
                        sent_at=n.sent_at,
                    )
                    for r in n.retries:
                        n_orm.retries.append(
                            EventRetryORM(
                                attempt=r.attempt, delay_s=r.delay, error=r.error
                            )
                        )
                    orm.notifications.append(n_orm)
                await session.commit()
        except Exception as exc:  # pragma: no cover - phụ thuộc DB runtime
            logger.warning("SqlEventStore persist lỗi {}: {}", record.event_id, exc)

    async def list_events(
        self, camera_id: Optional[int] = None, limit: int = 200
    ) -> List[EventRecordORM]:
        """Liệt kê event từ DB."""
        async with self._factory() as session:
            stmt = select(EventRecordORM).options(
                selectinload(EventRecordORM.notifications)
            )
            if camera_id is not None:
                stmt = stmt.where(EventRecordORM.camera_id == camera_id)
            stmt = stmt.order_by(EventRecordORM.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def _get(
        self, session: AsyncSession, event_id: str
    ) -> Optional[EventRecordORM]:
        stmt = (
            select(EventRecordORM)
            .options(selectinload(EventRecordORM.notifications))
            .where(EventRecordORM.event_id == event_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _apply(orm: EventRecordORM, record: EventRecord) -> None:
        orm.camera_id = record.camera_id
        orm.camera_name = record.camera_name
        orm.track_id = record.track_id
        orm.rule_id = record.rule_id
        orm.event_type = record.event_type
        orm.severity = record.severity
        orm.confidence = record.confidence
        orm.status = record.status.value
        orm.started_at = record.start_time
        orm.ended_at = record.end_time
        orm.duration_s = record.duration
        orm.roi = record.roi
        orm.snapshot_path = record.snapshot.path if record.snapshot else None
        orm.video_path = record.video.path if record.video else None
        orm.error = record.error
        orm.event_metadata = record.metadata
