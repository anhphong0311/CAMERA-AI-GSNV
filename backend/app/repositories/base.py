"""
Generic Repository Pattern — trừu tượng hóa truy cập database.

Tuân thủ Repository Pattern: service layer không trực tiếp query SQLAlchemy,
mà gọi qua repository để dễ test và thay đổi persistence layer.
"""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Repository cơ sở với CRUD cơ bản.

    Attributes:
        model: SQLAlchemy model class.
        session: AsyncSession inject từ FastAPI dependency.
    """

    def __init__(self, model: Type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: int | str) -> Optional[ModelT]:
        """
        Lấy một bản ghi theo primary key.

        Args:
            entity_id: Giá trị primary key.

        Returns:
            Model instance hoặc None nếu không tồn tại.
        """
        return await self.session.get(self.model, entity_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelT]:
        """
        Lấy danh sách bản ghi có phân trang.

        Args:
            skip: Số bản ghi bỏ qua.
            limit: Số bản ghi tối đa trả về.

        Returns:
            List các model instance.
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, entity: ModelT) -> ModelT:
        """
        Thêm bản ghi mới vào session (chưa commit).

        Args:
            entity: Model instance cần lưu.

        Returns:
            Entity đã add vào session.
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        """
        Xóa bản ghi khỏi database.

        Args:
            entity: Model instance cần xóa.
        """
        await self.session.delete(entity)
        await self.session.flush()
