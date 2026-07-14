"""
Kết nối PostgreSQL bất đồng bộ qua SQLAlchemy 2.0 + asyncpg.

Cung cấp engine, session factory và dependency `get_db_session`
để inject vào FastAPI routes (Dependency Injection).
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import get_settings


class Base(DeclarativeBase):
    """
    Lớp cơ sở cho tất cả SQLAlchemy ORM models.

    Alembic sử dụng metadata của lớp này để sinh migration.
    """

    pass


# Engine và session factory — khởi tạo lazy qua init_db()
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db() -> None:
    """
    Khởi tạo async engine và session factory.

    Gọi một lần khi ứng dụng startup (trong lifespan của FastAPI).
    """
    global _engine, _session_factory
    settings = get_settings()

    _engine = create_async_engine(
        str(settings.database_url),
        echo=settings.debug,
        pool_pre_ping=settings.db_pool_pre_ping,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


def get_engine() -> AsyncEngine:
    """
    Trả về async engine đã khởi tạo.

    Raises:
        RuntimeError: Nếu init_db() chưa được gọi.
    """
    if _engine is None:
        raise RuntimeError("Database chưa được khởi tạo. Gọi init_db() trước.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Trả về session factory để tạo AsyncSession.

    Raises:
        RuntimeError: Nếu init_db() chưa được gọi.
    """
    if _session_factory is None:
        raise RuntimeError("Database chưa được khởi tạo. Gọi init_db() trước.")
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency FastAPI — cung cấp AsyncSession trong scope request.

    Tự động commit nếu không có exception, rollback nếu có lỗi,
    và đóng session sau khi request kết thúc.

    Yields:
        AsyncSession: Phiên làm việc với database.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db() -> None:
    """Đóng engine khi ứng dụng shutdown."""
    if _engine is not None:
        await _engine.dispose()
