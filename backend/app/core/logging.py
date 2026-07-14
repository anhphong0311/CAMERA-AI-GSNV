"""
Thiết lập logging tập trung bằng Loguru.

Ghi log ra stdout (cho Docker) và file rotating trong thư mục logs/.
"""

import sys
from pathlib import Path

from loguru import logger

from app.config.settings import get_settings


def setup_logging() -> None:
    """
    Cấu hình Loguru cho toàn bộ ứng dụng.

    - Xóa handler mặc định.
    - Thêm handler stdout với format có màu (dev).
    - Thêm handler ghi file rotating (production/debug).
    """
    settings = get_settings()

    # Xóa handler mặc định của loguru
    logger.remove()

    # Log ra console — phù hợp Docker/K8s thu thập stdout
    if settings.environment == "production":
        # Structured JSON log cho production (ELK/Loki)
        logger.add(
            sys.stdout,
            level=settings.log_level,
            serialize=True,
            format="{message}",
        )
    else:
        logger.add(
            sys.stdout,
            level=settings.log_level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True,
        )

    # Ghi file rotating — retention theo env (production: 90 ngày)
    log_path = Path(settings.log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    retention = "90 days" if settings.environment == "production" else "30 days"
    logger.add(
        log_path / "aems_{time:YYYY-MM-DD}.log",
        level=settings.log_level,
        rotation="00:00",
        retention=retention,
        compression="zip",
        encoding="utf-8",
        serialize=settings.environment == "production",
    )
    # Error log riêng (production)
    if settings.environment == "production":
        logger.add(
            log_path / "error_{time:YYYY-MM-DD}.log",
            level="ERROR",
            rotation="00:00",
            retention=retention,
            compression="zip",
            serialize=True,
        )

    logger.info(
        "Logging initialized | env={} level={}",
        settings.environment,
        settings.log_level,
    )
