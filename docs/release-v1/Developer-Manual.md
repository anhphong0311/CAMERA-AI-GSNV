# Developer Manual — AEMS v1.0.0

## Project Structure

```
backend/app/modules/   # 10 domain modules (isolated)
backend/app/api/v1/    # HTTP routes (thin layer)
frontend/src/          # React SPA
config/                # Runtime YAML
deploy/                # Production scripts
```

## Architecture Rules

1. Modules communicate via service/API layer only
2. No cross-module direct database access
3. Repository pattern for data access
4. Dependency injection via FastAPI `app.state`

## Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm ci && npm run dev

# Tests
cd backend && pytest --cov=app --cov-config=.coveragerc -q
```

## Adding a Module

1. Create `backend/app/modules/your_module/`
2. Add `dependencies.py` with init/shutdown
3. Wire in `main.py` lifespan
4. Add API routes in `app/api/v1/`
5. Add tests in `tests/modules/your_module/`

## Code Quality

```bash
ruff check app tests
bandit -r app -ll
pytest --cov=app --cov-config=.coveragerc
```

## API Documentation

- Swagger: `/api/v1/docs`
- ReDoc: `/api/v1/redoc`
- OpenAPI JSON: `/api/v1/openapi.json`

## Database Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Static Analysis Config

- `backend/pyproject.toml` — Ruff, Bandit
- `backend/.coveragerc` — Coverage 90% gate
- `frontend/eslint.config.js` — ESLint

## Module READMEs

Each module has documentation in `backend/app/modules/{module}/README.md`
