# Backend — Sprint 1

## Cấu trúc (Clean Architecture)

```
app/
├── api/v1/          # HTTP routes (thin layer)
├── config/          # Pydantic Settings
├── core/            # DB, Redis, Security, Logging
├── dependencies/    # FastAPI DI
├── exceptions/      # Custom errors + handlers
├── middleware/      # CORS, request logging
├── models/          # SQLAlchemy ORM
├── repositories/    # Data access (Repository Pattern)
├── schemas/         # Pydantic request/response
├── services/        # Business logic (skeleton Sprint 1)
└── utils/
```

## Chạy local

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
copy .env.example .env
# Chỉnh DATABASE_URL, REDIS_* cho localhost
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Migration

```bash
alembic upgrade head
```

## API Docs

http://localhost:8000/api/v1/docs
