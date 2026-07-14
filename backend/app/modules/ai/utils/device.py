"""
Tiện ích chọn thiết bị inference — lazy import torch để module import an toàn.
"""

from loguru import logger


def resolve_device(preferred: str = "auto") -> str:
    """
    Xác định thiết bị chạy inference.

    Args:
        preferred: 'auto' | 'cpu' | 'cuda' | 'cuda:0' ...

    Returns:
        str: Thiết bị thực tế. Nếu yêu cầu CUDA nhưng không có → fallback cpu.
    """
    if preferred and preferred not in ("auto", "cuda") and not preferred.startswith("cuda"):
        # Chỉ định rõ cpu hoặc thiết bị cụ thể không phải cuda
        return preferred

    try:
        import torch

        if torch.cuda.is_available():
            device = "cuda:0" if preferred in ("auto", "cuda") else preferred
            logger.info("CUDA khả dụng | device={}", device)
            return device
        logger.info("CUDA không khả dụng — dùng CPU")
    except Exception as exc:  # torch chưa cài hoặc lỗi
        logger.warning("Không kiểm tra được CUDA ({}) — dùng CPU", exc)
    return "cpu"
