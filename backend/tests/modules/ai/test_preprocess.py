"""
Unit tests — ImagePreprocessor (validate, letterbox, normalize).
"""

import numpy as np
import pytest

from app.modules.ai.exceptions import InvalidFrameError
from app.modules.ai.preprocess import ImagePreprocessor


class TestImagePreprocessor:
    """Test tiền xử lý ảnh."""

    def test_validate_none_raises(self) -> None:
        """Frame None → InvalidFrameError."""
        pre = ImagePreprocessor(640)
        with pytest.raises(InvalidFrameError):
            pre.validate(None)  # type: ignore[arg-type]

    def test_validate_wrong_shape_raises(self) -> None:
        """Frame sai shape → InvalidFrameError."""
        pre = ImagePreprocessor(640)
        with pytest.raises(InvalidFrameError):
            pre.validate(np.zeros((100, 100), dtype=np.uint8))

    def test_letterbox_output_square(self) -> None:
        """Letterbox trả ảnh vuông image_size."""
        pre = ImagePreprocessor(640)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        padded, meta = pre.letterbox(frame)
        assert padded.shape[0] == 640
        assert padded.shape[1] == 640
        assert meta.orig_w == 640
        assert meta.orig_h == 480
        assert 0 < meta.ratio <= 1

    def test_letterbox_ratio_correct(self) -> None:
        """Ratio = min(size/w, size/h)."""
        pre = ImagePreprocessor(320)
        frame = np.zeros((160, 640, 3), dtype=np.uint8)
        _, meta = pre.letterbox(frame)
        assert meta.ratio == pytest.approx(320 / 640)

    def test_normalize_chw_range(self) -> None:
        """Normalize → float32 CHW trong [0,1]."""
        pre = ImagePreprocessor(64)
        frame = np.full((64, 64, 3), 255, dtype=np.uint8)
        tensor = pre.normalize(frame)
        assert tensor.shape == (3, 64, 64)
        assert tensor.dtype == np.float32
        assert tensor.max() <= 1.0

    def test_prepare_pipeline(self) -> None:
        """prepare trả tensor CHW + meta."""
        pre = ImagePreprocessor(640)
        frame = np.zeros((300, 500, 3), dtype=np.uint8)
        tensor, meta = pre.prepare(frame)
        assert tensor.shape == (3, 640, 640)
        assert meta.orig_w == 500
