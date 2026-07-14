"""Detection package — multi-camera pipeline + queue."""

from app.modules.ai.detection.frame_queue import AIFrameQueue, QueuedFrame
from app.modules.ai.detection.pipeline import DetectionPipeline

__all__ = ["AIFrameQueue", "DetectionPipeline", "QueuedFrame"]
