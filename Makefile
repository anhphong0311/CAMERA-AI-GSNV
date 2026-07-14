# =============================================================================
# AEMS - Makefile tiện ích (chạy được trên Git Bash / WSL / Linux / macOS).
# Trên PowerShell thuần, dùng trực tiếp lệnh docker compose tương ứng.
# =============================================================================

.PHONY: help up down build logs migrate revision be-shell fe-shell fmt lint

help:            ## Hiển thị danh sách lệnh
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up:              ## Khởi động toàn bộ stack
	docker compose up -d --build

down:            ## Dừng và xóa container
	docker compose down

build:           ## Build lại image
	docker compose build

logs:            ## Xem log realtime
	docker compose logs -f

migrate:         ## Chạy migration mới nhất
	docker compose exec backend alembic upgrade head

revision:        ## Tạo migration tự động (m="message")
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

be-shell:        ## Mở shell trong container backend
	docker compose exec backend bash

fe-shell:        ## Mở shell trong container frontend
	docker compose exec frontend sh

fmt:             ## Format code backend
	docker compose exec backend ruff format app

lint:            ## Lint code backend
	docker compose exec backend ruff check app
