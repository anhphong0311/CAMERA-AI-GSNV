"""Config package — AI Detection Engine."""

from app.modules.ai.config.loader import (
    ClassConfig,
    DetectionConfig,
    ModelConfig,
    QueueConfig,
    load_detection_config,
)

__all__ = [
    "ClassConfig",
    "DetectionConfig",
    "ModelConfig",
    "QueueConfig",
    "load_detection_config",
]
