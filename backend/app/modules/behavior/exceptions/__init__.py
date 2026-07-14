"""Exceptions package — Behavior Feature Engine."""

from app.modules.behavior.exceptions.errors import (
    BehaviorException,
    BufferOverflowError,
    InvalidSkeletonError,
    MissingJointError,
    PoseError,
    PoseModelLoadError,
    PoseModelNotLoadedError,
)

__all__ = [
    "BehaviorException",
    "BufferOverflowError",
    "InvalidSkeletonError",
    "MissingJointError",
    "PoseError",
    "PoseModelLoadError",
    "PoseModelNotLoadedError",
]
