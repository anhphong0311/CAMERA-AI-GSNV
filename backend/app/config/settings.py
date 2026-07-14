"""
Module cấu hình ứng dụng.

Sử dụng Pydantic Settings để đọc biến môi trường từ `.env`,
đảm bảo không hardcode secret hoặc tham số hạ tầng trong code.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Lớp cấu hình tập trung cho toàn bộ backend.

    Mọi giá trị được nạp từ biến môi trường hoặc file `.env`.
    Singleton được tạo qua `get_settings()` để tái sử dụng (DRY).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- Thông tin dự án -----
    project_name: str = Field(default="AEMS", alias="PROJECT_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")

    # ----- PostgreSQL -----
    postgres_user: str = Field(default="aems", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="aems", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_url: PostgresDsn | str = Field(
        default="postgresql+asyncpg://aems:aems@localhost:5432/aems",
        alias="DATABASE_URL",
    )

    # ----- Redis -----
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    # ----- JWT / Bảo mật -----
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_minutes: int = Field(
        default=10080, alias="REFRESH_TOKEN_EXPIRE_MINUTES"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    # ----- Enterprise Admin (Sprint 9) -----
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="Admin@12345", alias="ADMIN_PASSWORD")
    admin_email: str = Field(default="admin@aems.local", alias="ADMIN_EMAIL")
    admin_use_sql: bool = Field(default=False, alias="ADMIN_USE_SQL")
    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")

    # ----- Performance / DB pool (Sprint 10) -----
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_pre_ping: bool = Field(default=True, alias="DB_POOL_PRE_PING")

    # ----- Server -----
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    backend_cors_origins: str = Field(
        default="http://localhost:5173",
        alias="BACKEND_CORS_ORIGINS",
    )

    # ----- Logging -----
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: str = Field(default="../logs", alias="LOG_DIR")

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | List[str]) -> str:
        """Chuẩn hóa CORS origins — giữ dạng chuỗi, parse khi dùng."""
        if isinstance(value, list):
            return ",".join(value)
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Trả về danh sách origin được phép cho CORS middleware.

        Returns:
            List[str]: Các URL frontend hợp lệ.
        """
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]

    @property
    def redis_url(self) -> str:
        """
        Xây dựng URL kết nối Redis từ các thành phần cấu hình.

        Returns:
            str: URL dạng redis://[:password@]host:port/db
        """
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:"
                f"{self.redis_port}/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_development(self) -> bool:
        """Kiểm tra môi trường development."""
        return self.environment.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Factory singleton cho Settings (Dependency Injection friendly).

    Dùng lru_cache để chỉ parse `.env` một lần trong vòng đời process.

    Returns:
        Settings: Instance cấu hình đã cache.
    """
    return Settings()
