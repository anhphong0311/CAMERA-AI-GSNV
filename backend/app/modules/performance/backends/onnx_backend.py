"""
ONNX Runtime backend — Sprint 10.

Chạy YOLO đã export sang ONNX. Hỗ trợ CUDAExecutionProvider khi có GPU.
Không thay đổi output contract (List[RawDetection]).
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np

from app.modules.ai.inference.backend import InferenceBackend
from app.modules.ai.models import RawDetection


# COCO 80 class names (subset used by AEMS)
_COCO_NAMES = {
    0: "person", 39: "bottle", 41: "cup", 56: "chair", 62: "monitor",
    63: "laptop", 64: "mouse", 66: "keyboard", 67: "cell phone",
}


def _letterbox(img: np.ndarray, new_size: int) -> tuple[np.ndarray, float, tuple[int, int]]:
    """Letterbox resize giữ tỷ lệ."""
    h, w = img.shape[:2]
    scale = min(new_size / h, new_size / w)
    nh, nw = int(h * scale), int(w * scale)
    resized = np.ascontiguousarray(
        __import__("cv2").resize(img, (nw, nh), interpolation=__import__("cv2").INTER_LINEAR)
    )
    canvas = np.full((new_size, new_size, 3), 114, dtype=np.uint8)
    top = (new_size - nh) // 2
    left = (new_size - nw) // 2
    canvas[top : top + nh, left : left + nw] = resized
    return canvas, scale, (left, top)


def _nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> List[int]:
    """NMS đơn giản (CPU)."""
    if len(boxes) == 0:
        return []
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep: List[int] = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)
        if order.size == 1:
            break
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        order = order[1:][iou <= iou_threshold]
    return keep


class ONNXBackend(InferenceBackend):
    """Backend ONNX Runtime cho YOLO export."""

    def __init__(
        self,
        onnx_path: str,
        device: str = "cpu",
        half: bool = False,
        class_names: dict[int, str] | None = None,
    ) -> None:
        self._onnx_path = onnx_path
        self._device = device
        self._half = half
        self._session = None
        self._input_name = ""
        self._class_names = class_names or dict(_COCO_NAMES)

    def load(self) -> None:
        from app.modules.ai.exceptions import ModelLoadError

        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise ModelLoadError(f"onnxruntime chưa cài: {exc}") from exc

        providers: List[str | tuple] = ["CPUExecutionProvider"]
        if self._device.startswith("cuda"):
            providers = [
                ("CUDAExecutionProvider", {"device_id": int(self._device.split(":")[-1] or 0)}),
                "CPUExecutionProvider",
            ]
        try:
            self._session = ort.InferenceSession(self._onnx_path, providers=providers)
            self._input_name = self._session.get_inputs()[0].name
        except Exception as exc:
            raise ModelLoadError(f"Lỗi nạp ONNX: {exc}") from exc

    @property
    def device(self) -> str:
        return self._device

    @property
    def class_names(self) -> dict[int, str]:
        return self._class_names

    def predict(
        self,
        frame: np.ndarray,
        image_size: int,
        confidence: float,
        iou: float,
        allowed_class_ids: Sequence[int],
        half: bool,
    ) -> List[RawDetection]:
        from app.modules.ai.exceptions import InferenceError, ModelNotLoadedError

        if self._session is None:
            raise ModelNotLoadedError()

        try:
            lb, scale, (pad_x, pad_y) = _letterbox(frame, image_size)
            blob = lb.transpose(2, 0, 1)[None].astype(np.float32) / 255.0
            outputs = self._session.run(None, {self._input_name: blob})
            return self._parse_yolo_output(
                outputs[0], frame.shape[:2], scale, pad_x, pad_y,
                confidence, iou, allowed_class_ids,
            )
        except Exception as exc:
            raise InferenceError(str(exc)) from exc

    @staticmethod
    def _parse_yolo_output(
        output: np.ndarray,
        orig_shape: tuple[int, int],
        scale: float,
        pad_x: int,
        pad_y: int,
        conf_thresh: float,
        iou: float,
        allowed: Sequence[int],
    ) -> List[RawDetection]:
        """Parse YOLOv8/v11 ONNX output [1, 84, N] hoặc [1, N, 84]."""
        if output.ndim == 3:
            pred = output[0]
            if pred.shape[0] < pred.shape[1]:
                pred = pred.T  # [N, 84]
        else:
            pred = output.reshape(-1, output.shape[-1])

        if pred.shape[1] < 5:
            return []

        boxes_xywh = pred[:, :4]
        class_scores = pred[:, 4:]
        cls_ids = class_scores.argmax(axis=1)
        scores = class_scores.max(axis=1)
        mask = scores >= conf_thresh
        if allowed:
            allowed_set = set(allowed)
            mask &= np.isin(cls_ids, list(allowed_set))
        boxes_xywh = boxes_xywh[mask]
        scores = scores[mask]
        cls_ids = cls_ids[mask]
        if len(scores) == 0:
            return []

        # xywh → xyxy trong không gian letterbox
        x_c, y_c, w, h = boxes_xywh.T
        x1 = x_c - w / 2
        y1 = y_c - h / 2
        x2 = x_c + w / 2
        y2 = y_c + h / 2
        boxes = np.stack([x1, y1, x2, y2], axis=1)

        # Map về ảnh gốc
        boxes[:, [0, 2]] = (boxes[:, [0, 2]] - pad_x) / scale
        boxes[:, [1, 3]] = (boxes[:, [1, 3]] - pad_y) / scale
        oh, ow = orig_shape
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, ow)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, oh)

        keep = _nms(boxes, scores, iou)
        raws: List[RawDetection] = []
        for i in keep:
            raws.append(
                RawDetection(
                    class_id=int(cls_ids[i]),
                    confidence=float(scores[i]),
                    xyxy=(float(boxes[i, 0]), float(boxes[i, 1]), float(boxes[i, 2]), float(boxes[i, 3])),
                )
            )
        return raws

    def warmup(self, image_size: int, iterations: int = 3) -> None:
        if self._session is None:
            return
        dummy = np.zeros((image_size, image_size, 3), dtype=np.uint8)
        for _ in range(max(0, iterations)):
            self.predict(dummy, image_size, 0.25, 0.45, list(_COCO_NAMES.keys()), self._half)

    def release(self) -> None:
        self._session = None
