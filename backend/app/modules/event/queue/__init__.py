"""Queue package — Event Processing Center."""

from app.modules.event.queue.queues import BoundedQueue

__all__ = ["BoundedQueue"]
