# Folder Structure Report

## Actual monorepo layout

```
CAM-GSNV/
├── backend/          # FastAPI + domain modules (ai, camera, event, rule_engine, …)
├── frontend/         # React + Vite dashboard
├── config/           # Runtime YAML (mounted into containers)
├── docs/             # Specs, sprint docs, reports
├── deploy/           # Install scripts, systemd, grafana, docker helpers
├── docker/           # Nginx
├── models/           # Weights (gitignored; auto-download)
├── data/             # Evidence mount
├── logs/             # Rotating logs + system_state.json
├── docker-compose.yml
└── docker-compose.production.yml
```

## Phase 13 (restructure to flat `ai/`, `camera/`, `routers/`)

**Not executed.** A full folder rename would:

- Break every import path  
- Risk behavioral regressions  
- Violate “no behavior change” without multi-week migration  

Current `backend/app/modules/*` domain boundaries are already clear and intentional.

## Stale docs note

Some docs mention root `ai-worker/`, `agent/`, `infra/` trees that are **not present** as code; AI worker lives under `backend/app/modules/ops/` and deploy Docker. Docs drift only — no code delete.
