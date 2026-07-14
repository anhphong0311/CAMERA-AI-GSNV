"""Label classes và cấu hình mặc định cho ML Platform."""

from __future__ import annotations

from typing import List, Literal

# Nhãn chuẩn AEMS (COCO-style office objects)
LABEL_CLASSES: List[str] = [
    "person",
    "phone",
    "cup",
    "bottle",
    "food",
    "chair",
    "laptop",
    "keyboard",
    "mouse",
    "monitor",
]

AnnotationTool = Literal["internal", "cvat", "label_studio", "roboflow"]
ModelArchitecture = Literal["yolo11", "yolo12", "rt-detr", "custom"]
DatasetSource = Literal["image", "video", "snapshot", "event", "false_positive", "false_negative"]

SUPPORTED_ARCHITECTURES: List[str] = ["yolo11", "yolo12", "rt-detr", "custom"]
SUPPORTED_ANNOTATION_TOOLS: List[str] = ["internal", "cvat", "label_studio", "roboflow"]

DEFAULT_TRAIN_CONFIG = {
    "batch_size": 16,
    "epochs": 100,
    "learning_rate": 0.001,
    "optimizer": "AdamW",
    "scheduler": "cosine",
    "image_size": 640,
    "augmentation": {
        "flip": True,
        "rotation": 15,
        "brightness": 0.2,
        "contrast": 0.2,
        "blur": 0.1,
        "noise": 0.05,
        "crop": True,
        "mosaic": True,
        "mixup": 0.1,
    },
    "mixed_precision": True,
    "device": "cuda",
}
