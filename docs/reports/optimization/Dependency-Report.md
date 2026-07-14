# Dependency Report

## Python (`backend/requirements.txt`)

| Package | Used? | Action |
|---------|-------|--------|
| fastapi, uvicorn, sqlalchemy, asyncpg, alembic | YES | Keep |
| pydantic, pydantic-settings | YES | Keep |
| python-jose, passlib | YES (admin security) | Keep |
| redis, loguru, httpx, pyyaml | YES | Keep |
| opencv-python-headless, numpy, ultralytics, psutil | YES | Keep |
| onnxruntime | YES (performance backends) | Keep |
| python-multipart | No UploadFile in app, but FastAPI form/file stack often needs it | **Keep (MAYBE unused)** |
| email-validator | No EmailStr in app | **Keep (MAYBE unused)** — do not remove without form audit |

`requirements-dev.txt`: pytest, ruff, bandit, psycopg2 — keep for CI/local.

## Node (`frontend/package.json`)

| Package | Used? | Action |
|---------|-------|--------|
| `date-fns` | 0 imports | **Removed** |
| `@radix-ui/react-popover` | 0 imports / no component | **Removed** |
| `@radix-ui/react-scroll-area` | 0 imports / no component | **Removed** |
| `@radix-ui/react-separator` | Only dead `separator.tsx` | **Removed** with component |
| Remaining Radix / react / charts / export libs | YES | Keep |
| `prettier` (dev) | IDE/format; no npm script | Keep |

## Circular dependencies

No hard runtime circular imports found. ORM relations use `TYPE_CHECKING`. Cross-module wiring via `app.state` + `getattr`.
