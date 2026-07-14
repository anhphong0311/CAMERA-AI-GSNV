"""Performance factory tests (Sprint 12 QA)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.performance.backends.factory import create_backend


def test_create_backend_invalid_type():
    with pytest.raises(ValueError, match="Backend không hỗ trợ"):
        create_backend(
            "invalid",  # type: ignore[arg-type]
            model_path="m.pt",
            onnx_path="m.onnx",
            tensorrt_path="m.trt",
            device="cpu",
            half=False,
        )


def test_create_backend_pytorch_mocked():
    mock_backend = MagicMock()
    with patch("app.modules.performance.backends.factory.UltralyticsBackend", return_value=mock_backend):
        backend = create_backend(
            "pytorch",
            model_path="m.pt",
            onnx_path="m.onnx",
            tensorrt_path="m.trt",
            device="cpu",
            half=False,
        )
    mock_backend.load.assert_called_once()
    assert backend is mock_backend
