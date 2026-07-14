"""
ModelRepository — Repository Pattern cho ARTIFACT model (file weight).

LƯU Ý: Đây KHÔNG phải database repository. Detection Engine độc lập,
không truy cập DB. Repository này trừu tượng hóa nơi lưu weight
(filesystem hiện tại; sau này có thể là MinIO/model registry) —
đổi nguồn lưu trữ không cần sửa business logic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List


class ModelRepository:
    """
    Quản lý truy xuất file weight model từ filesystem.

    Attributes:
        search_dirs: Các thư mục tìm model khi path là tương đối.
    """

    def __init__(self, search_dirs: List[str] | None = None) -> None:
        # Ưu tiên biến môi trường MODELS_DIR, rồi các vị trí mặc định.
        env_dir = os.getenv("MODELS_DIR")
        default_dirs = [
            "models",
            "/models",
            str(Path(__file__).resolve().parents[5] / "models"),
            str(Path(__file__).resolve().parents[4] / "models"),
        ]
        if env_dir:
            default_dirs.insert(0, env_dir)
        self.search_dirs = search_dirs or default_dirs

    def resolve(self, model_path: str) -> str:
        """
        Chuyển model_path thành đường dẫn tuyệt đối tồn tại.

        Nếu là đường dẫn tuyệt đối/tồn tại → trả nguyên.
        Nếu tương đối → tìm trong search_dirs.
        Nếu chỉ là tên weight chuẩn (vd yolo11n.pt) và không tìm thấy →
        trả về nguyên tên để Ultralytics tự tải về (auto-download).

        Args:
            model_path: Đường dẫn hoặc tên weight.

        Returns:
            str: Đường dẫn dùng để nạp model.
        """
        p = Path(model_path)
        if p.is_absolute() and p.exists():
            return str(p)
        if p.exists():
            return str(p.resolve())

        for d in self.search_dirs:
            candidate = Path(d) / p.name
            if candidate.exists():
                return str(candidate.resolve())

        # Không tìm thấy local — trả nguyên (Ultralytics auto-download weight chuẩn)
        return model_path

    def exists(self, model_path: str) -> bool:
        """
        Kiểm tra weight có sẵn local HOẶC là tên weight chuẩn (auto-download).

        Args:
            model_path: Đường dẫn/tên weight.

        Returns:
            bool: True nếu có thể nạp.
        """
        p = Path(model_path)
        if p.exists():
            return True
        for d in self.search_dirs:
            if (Path(d) / p.name).exists():
                return True
        # Tên weight chuẩn Ultralytics → cho phép auto-download
        return self._is_standard_weight(p.name)

    @staticmethod
    def _is_standard_weight(name: str) -> bool:
        """Nhận diện tên weight YOLO chuẩn (yolo11n.pt, yolov8s.pt...)."""
        lname = name.lower()
        return (
            lname.endswith(".pt")
            and (lname.startswith("yolo") or lname.startswith("yolov"))
        )

    def list_local_models(self) -> List[str]:
        """Liệt kê file weight có trong search_dirs (debug/quản trị)."""
        found: List[str] = []
        for d in self.search_dirs:
            path = Path(d)
            if path.is_dir():
                found.extend(str(f) for f in path.glob("*.pt"))
                found.extend(str(f) for f in path.glob("*.onnx"))
                found.extend(str(f) for f in path.glob("*.engine"))
        return found
