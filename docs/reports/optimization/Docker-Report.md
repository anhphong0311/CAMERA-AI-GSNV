# Docker Report

## Changes applied

| Item | Action |
|------|--------|
| `backend/.dockerignore` | **Added** — exclude `.venv`, tests caches, logs, backups |
| `frontend/.dockerignore` | **Added** — exclude `node_modules`, dist, e2e caches |
| `deploy/docker/ai-worker/Dockerfile` | **Deleted** (orphan; compose uses backend production Dockerfile) |

## Recommendations (not applied — optional)

1. Dev `backend/Dockerfile`: multi-stage; do not install `requirements-dev.txt` in runtime image  
2. Frontend dev Dockerfile: `npm ci` instead of `npm install`  
3. BuildKit cache mounts for pip/npm  
4. Future: split API image vs AI-worker image (torch/ultralytics size)

## Do not change

- Production compose topology  
- Mounted config volumes  
- Model volume `/models`  
