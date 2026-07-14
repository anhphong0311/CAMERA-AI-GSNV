"""
Unit tests — ReconnectPolicy backoff.
"""

import pytest

from app.modules.camera.reconnect.backoff import ReconnectPolicy


class TestReconnectPolicy:
    """Test exponential backoff reconnect."""

    def test_delays_sequence(self) -> None:
        """Delay theo thứ tự 1,3,5,10,30 rồi lặp 30."""
        policy = ReconnectPolicy([1, 3, 5, 10, 30])
        assert policy.next_delay() == 1.0
        assert policy.next_delay() == 3.0
        assert policy.next_delay() == 5.0
        assert policy.next_delay() == 10.0
        assert policy.next_delay() == 30.0
        assert policy.next_delay() == 30.0

    def test_reset_after_success(self) -> None:
        """Reset sau connect thành công."""
        policy = ReconnectPolicy([1, 3])
        policy.next_delay()
        policy.next_delay()
        policy.record_success()
        assert policy.attempt == 0
        assert policy.next_delay() == 1.0
