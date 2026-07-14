@echo off
REM Chạy Alembic migration trong Docker backend container
docker compose exec backend alembic upgrade head
