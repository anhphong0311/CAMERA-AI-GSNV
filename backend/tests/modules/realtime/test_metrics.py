from unittest.mock import MagicMock, patch

import sys

from app.modules.realtime import metrics


def test_collect_system_metrics_with_psutil_mock():
    mock_psutil = MagicMock()
    mock_psutil.cpu_percent.return_value = 25.0
    mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0, used=4e9, total=8e9)
    mock_psutil.disk_usage.return_value = MagicMock(percent=40.0, used=100e9, total=500e9)
    mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=2000)

    with patch.dict(sys.modules, {"psutil": mock_psutil}):
        data = metrics.collect_system_metrics()
    assert data["cpu_percent"] == 25.0
    assert data["ram_percent"] == 60.0
