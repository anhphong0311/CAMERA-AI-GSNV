# Cleanup Report

**Policy:** No file deleted unless reference count = 0 in production import graph. MAYBE items are marked only.

| File | Reason | Ref count (prod) | Safe To Delete | Action |
|------|--------|------------------|----------------|--------|
| `backend/app/api/v1/auth.py` | Unregistered; replaced by admin auth | 0 | YES | **Deleted** |
| `backend/app/api/v1/users.py` | Unregistered; replaced by admin users | 0 | YES | **Deleted** |
| `backend/app/services/auth_service.py` | Skeleton; only dead routers | 0 | YES | **Deleted** |
| `frontend/src/components/common/RoleGate.tsx` | Never imported | 0 | YES | **Deleted** |
| `frontend/src/components/ui/skeleton.tsx` | Never imported | 0 | YES | **Deleted** |
| `frontend/src/components/ui/separator.tsx` | Never imported | 0 | YES | **Deleted** |
| `deploy/docker/ai-worker/Dockerfile` | Compose uses `backend/Dockerfile.production` | 0 | YES | **Deleted** |
| `backend/app/modules/event/video_recorder/*` | Runtime unused; tests still import | tests only | MAYBE | **Kept** |
| `backend/app/modules/*/utils/visualizer.py` | Debug / integration tests | tests only | MAYBE | **Kept** |
| `backend/app/models/log.py` | No service usage yet | ORM export | MAYBE | **Kept** |
| `backend/app/api/v1/employees.py` etc. | Skeleton but **registered** | live routes | NO | **Kept** |
| `config/*.yaml` | All loaded / mounted | 1+ | NO | **Kept** |
| `models/*` weights | Runtime AI | N/A | NO | **Kept** |
| `.env*`, compose, migrations | Critical | N/A | NO | **Kept** |
| `*.bak` / `*.old` / `*.tmp` | None found | 0 | N/A | — |
| `logs/*.log` | Runtime rotatable | 0 code | local prune OK | **Not deleted by agent** |
| `backend/data/backups/*.json` | Local snapshots | 0 | local prune OK | **Not deleted by agent** |

## Kept with reason

| File | Why kept |
|------|----------|
| `ops/watchdog.py`, `ops/ai_worker.py` | Deploy entrypoints |
| All `config/*.yaml` | Mounted + loaders |
| Skeleton `employees`/`alerts`/`dashboard` | Still in OpenAPI; removing = API break |
| Evidence / camera buffers (tuned, not removed) | Required for preview + snapshots |
