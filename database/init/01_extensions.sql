-- Database init script — chạy khi PostgreSQL container khởi tạo lần đầu.
-- Bật extension cần thiết cho UUID.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Alembic migration sẽ tạo bảng; script này chỉ chuẩn bị extension.
-- Seed dữ liệu mặc định (roles, admin) sẽ thêm ở sprint 2.
