"""
Export tất cả ORM models — Alembic env.py import module này
để autogenerate migration và đảm bảo metadata đầy đủ.
"""

from app.models.admin import (
    AuditLog,
    BackupRecord,
    ConfigEntry,
    ModelVersion,
    ScheduledJobRecord,
    UserSession,
)
from app.models.alert import Alert, Notification, Snapshot, Video
from app.models.camera import Camera, Zone
from app.models.employee import Department, Employee
from app.models.event_processing import (
    EventNotificationORM,
    EventRecordORM,
    EventRetryORM,
)
from app.models.log import Log
from app.models.performance_score import PerformanceScore
from app.models.rule import Rule
from app.models.tracking import Detection, Tracking
from app.models.user import Permission, Role, RolePermission, User
from app.models.ml_platform import (
    MLDataset,
    MLDatasetVersion,
    MLFpFnCase,
    MLTrainingEpoch,
    MLTrainingJob,
)

__all__ = [
    "AuditLog",
    "ConfigEntry",
    "ModelVersion",
    "UserSession",
    "BackupRecord",
    "ScheduledJobRecord",
    "EventRecordORM",
    "EventNotificationORM",
    "EventRetryORM",
    "Permission",
    "Role",
    "RolePermission",
    "User",
    "Department",
    "Employee",
    "Camera",
    "Zone",
    "Rule",
    "Tracking",
    "Detection",
    "Alert",
    "Snapshot",
    "Video",
    "Notification",
    "PerformanceScore",
    "Log",
    "MLDataset",
    "MLDatasetVersion",
    "MLTrainingJob",
    "MLTrainingEpoch",
    "MLFpFnCase",
]
