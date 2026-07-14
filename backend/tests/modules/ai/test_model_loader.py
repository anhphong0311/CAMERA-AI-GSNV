"""
Unit tests — ModelLoader (verify, load, warmup, reload, release).

Patch UltralyticsBackend để không cần torch/ultralytics thật.
"""

import pytest

from app.modules.ai.exceptions import ModelNotFoundError
from app.modules.ai.inference.model_loader import ModelLoader
from app.modules.ai.repositories.model_repository import ModelRepository


class _FakeBackend:
    """Backend giả thay UltralyticsBackend trong ModelLoader."""

    def __init__(self, model_path: str, device: str, half: bool) -> None:
        self.model_path = model_path
        self.device = device
        self.half = half
        self.loaded = False
        self.warmup_calls = 0
        self.released = False

    def load(self) -> None:
        self.loaded = True

    def warmup(self, image_size: int, iterations: int = 3) -> None:
        self.warmup_calls += iterations

    def release(self) -> None:
        self.released = True


@pytest.fixture
def patch_backend(monkeypatch):
    """Thay UltralyticsBackend bằng _FakeBackend."""
    monkeypatch.setattr(
        "app.modules.ai.inference.model_loader.UltralyticsBackend", _FakeBackend
    )


class TestModelLoaderVerify:
    """Test verify weight tồn tại."""

    def test_verify_missing_non_standard_raises(self) -> None:
        """File không tồn tại và không phải weight chuẩn → ModelNotFoundError."""
        repo = ModelRepository(search_dirs=[])
        loader = ModelLoader(
            model_path="does_not_exist.bin",
            model_name="custom",
            device="cpu",
            repository=repo,
        )
        with pytest.raises(ModelNotFoundError):
            loader.verify()

    def test_verify_standard_weight_ok(self) -> None:
        """Tên weight chuẩn (yolo11n.pt) → cho phép (auto-download)."""
        repo = ModelRepository(search_dirs=[])
        loader = ModelLoader(
            model_path="yolo11n.pt",
            model_name="yolo11n",
            device="cpu",
            repository=repo,
        )
        loader.verify()  # không raise


class TestModelLoaderLifecycle:
    """Test load/warmup/reload/release với backend giả."""

    def _make_loader(self) -> ModelLoader:
        return ModelLoader(
            model_path="yolo11n.pt",
            model_name="yolo11n",
            device="cpu",
            image_size=640,
            class_labels=["person", "phone"],
            repository=ModelRepository(search_dirs=[]),
        )

    def test_load_sets_loaded_and_warmup(self, patch_backend) -> None:
        """load() → is_loaded True, warmup_done True."""
        loader = self._make_loader()
        info = loader.load(warmup_iterations=2)
        assert loader.is_loaded
        assert info.loaded is True
        assert info.warmup_done is True
        assert info.device == "cpu"

    def test_get_info_labels(self, patch_backend) -> None:
        """ModelInfo giữ class labels."""
        loader = self._make_loader()
        loader.load(warmup_iterations=0)
        info = loader.get_info()
        assert "person" in info.class_labels

    def test_release_unloads(self, patch_backend) -> None:
        """release() → is_loaded False."""
        loader = self._make_loader()
        loader.load(warmup_iterations=0)
        loader.release()
        assert not loader.is_loaded
        assert loader.get_info().loaded is False

    def test_reload_reloads(self, patch_backend) -> None:
        """reload() → model loaded lại."""
        loader = self._make_loader()
        loader.load(warmup_iterations=0)
        info = loader.reload(warmup_iterations=1)
        assert info.loaded is True
        assert loader.is_loaded
