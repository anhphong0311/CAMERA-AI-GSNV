"""Services package — AI Detection Engine."""

from app.modules.ai.services.benchmark_service import BenchmarkService
from app.modules.ai.services.detection_service import (
    DetectionService,
    DetectionStatistics,
)

__all__ = ["BenchmarkService", "DetectionService", "DetectionStatistics"]
