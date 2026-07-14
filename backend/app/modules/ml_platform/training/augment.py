"""Data augmentation config — ML Platform."""

from __future__ import annotations

from typing import Any, Dict


def default_augmentation() -> Dict[str, Any]:
    return {
        "flip": True,
        "rotation_deg": 15,
        "brightness": 0.2,
        "contrast": 0.2,
        "blur_prob": 0.1,
        "noise_prob": 0.05,
        "random_crop": True,
        "mosaic": True,
        "mixup": 0.1,
    }


def merge_augmentation(overrides: Dict[str, Any] | None) -> Dict[str, Any]:
    cfg = default_augmentation()
    if overrides:
        cfg.update(overrides)
    return cfg


def describe_augmentation(cfg: Dict[str, Any]) -> str:
    enabled = [k for k, v in cfg.items() if v and v != 0]
    return ", ".join(enabled) if enabled else "none"
