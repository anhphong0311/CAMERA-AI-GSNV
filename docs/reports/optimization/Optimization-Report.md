# Optimization & Cleanup Sprint — Master Report

**Date:** 2026-07-14  
**Scope:** CAM-GSNV (AEMS) — performance, dead-code cleanup, standardization  
**Constraints honored:** No new features · No Rule Engine changes · No business-logic changes · No DB schema changes · No unsafe deletes

---

## Executive Summary

| Area | Finding | Action taken |
|------|---------|--------------|
| Dead API routers | `auth.py`, `users.py` unregistered (replaced by admin) | **Deleted** |
| Skeleton AuthService | Only used by dead routers | **Deleted** + DI cleaned |
| Frontend deps | `date-fns`, popover, scroll-area unused | **Removed** |
| Dead UI | `RoleGate`, `Skeleton`, `Separator` | **Deleted** |
| Orphan Dockerfile | `deploy/docker/ai-worker/Dockerfile` unused by compose | **Deleted** |
| Camera RAM | `queue_size`/`buffer_size` 450 ≈ huge per-camera frames | **Tuned → 45** (preview only needs latest) |
| Duplicate evidence push | Camera sink + AI bridge both `push_frame` | **Removed bridge duplicate** |
| Docker build | No `.dockerignore` | **Added** backend + frontend |
| Rule Engine / API contract / migrations | — | **Untouched** |

---

## Phase reports (this folder)

| Report | File |
|--------|------|
| Cleanup Report | [Cleanup-Report.md](./Cleanup-Report.md) |
| Dependency Report | [Dependency-Report.md](./Dependency-Report.md) |
| Performance / Memory | [Performance-Memory-Report.md](./Performance-Memory-Report.md) |
| Docker Report | [Docker-Report.md](./Docker-Report.md) |
| Folder Structure | [Folder-Structure-Report.md](./Folder-Structure-Report.md) |

---

## Validation checklist

| Check | Status |
|-------|--------|
| Rule Engine unchanged | ✓ |
| Business rules / `rules.yaml` logic unchanged | ✓ (thresholds not part of this sprint's rule code) |
| DB schema / migrations unchanged | ✓ |
| Telegram / Camera / YOLO / ByteTrack paths intact | ✓ |
| Dead code removed only with 0 production refs | ✓ |
| MAYBE items left marked, not deleted | ✓ |

---

## Follow-up recommendations (NOT done — needs explicit approval)

1. Consolidate `event/video_recorder/` into `evidence/` after migrating tests  
2. Wire or deprecate skeleton `/employees`, `/alerts`, `/dashboard` stubs  
3. Split API-only vs AI-worker Docker images (GB-scale torch)  
4. Optional: reduce evidence buffer FPS if CPU-bound (trade-off vs video quality)  
5. Profile live FPS/CPU/RAM before/after on production host for numeric Phase 12 metrics  
