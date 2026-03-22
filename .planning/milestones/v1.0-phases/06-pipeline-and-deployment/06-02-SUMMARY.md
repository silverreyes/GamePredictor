---
phase: 06-pipeline-and-deployment
plan: 02
subsystem: infra
tags: [docker, nginx, docker-compose, multi-stage-build, entrypoint]

# Dependency graph
requires:
  - phase: 06-pipeline-and-deployment (plan 01)
    provides: MLflow-free codebase ready for containerization
provides:
  - Complete Docker infrastructure: 4-service compose (postgres, api, worker, nginx)
  - Multi-stage nginx.Dockerfile for frontend build + serving
  - Entrypoint-based model volume seeding on first boot
  - App nginx config routing /api/ to FastAPI and serving SPA
affects: [06-03 VPS deployment guide]

# Tech tracking
tech-stack:
  added: [nginx-alpine, node-20-alpine multi-stage]
  patterns: [entrypoint volume seeding, multi-stage Docker builds, compose service health dependencies]

key-files:
  created:
    - docker/entrypoint.sh
    - docker/nginx.conf
    - docker/nginx.Dockerfile
    - .gitattributes
  modified:
    - Dockerfile
    - docker-compose.yml
    - .dockerignore
    - .env.example

key-decisions:
  - "Added .gitattributes to enforce LF line endings for shell scripts (prevents CRLF corruption in Docker builds on Windows)"

patterns-established:
  - "Entrypoint pattern: volume seeding on first boot via conditional cp in entrypoint.sh"
  - "Two-layer nginx: app nginx container on port 8080, VPS system nginx as reverse proxy"
  - "Multi-stage frontend build: Node 20 Alpine builds React, nginx Alpine serves static files"

requirements-completed: [PIPE-03, PIPE-04]

# Metrics
duration: 2min
completed: 2026-03-22
---

# Phase 06 Plan 02: Docker Infrastructure Summary

**4-service Docker Compose stack (postgres, api, worker, nginx) with entrypoint-based model seeding, multi-stage frontend build, and app nginx routing**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-22T20:49:34Z
- **Completed:** 2026-03-22T20:52:05Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Created docker/ directory with entrypoint.sh (volume seeding), nginx.conf (API proxy + SPA fallback), and nginx.Dockerfile (multi-stage Node->nginx build)
- Rewrote docker-compose.yml from 5 services/4 volumes to 4 services/2 volumes (removed mlflow, caddy, mlartifacts, caddy_data)
- Updated Dockerfile with ENTRYPOINT directive for volume seeding wrapper
- Updated .env.example (removed DOMAIN, kept 3 essential vars) and .dockerignore (added frontend/dist exclusion)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create docker/ directory files** - `c0d73fb` (feat)
2. **Task 2: Update Dockerfile, rewrite docker-compose.yml, update configs** - `04200b1` (feat)

**Deviation fix:** `4c724a6` (fix: .gitattributes for LF enforcement)

## Files Created/Modified
- `docker/entrypoint.sh` - Seeds models volume on first boot (copies best_model.json and experiments.jsonl)
- `docker/nginx.conf` - Routes /api/ to api:8000, serves SPA with try_files fallback
- `docker/nginx.Dockerfile` - Multi-stage: Node 20 Alpine builds React frontend, nginx Alpine serves static files
- `Dockerfile` - Added entrypoint.sh COPY, chmod, and ENTRYPOINT directive
- `docker-compose.yml` - 4 services (postgres, api, worker, nginx), 2 volumes (pgdata, models)
- `.dockerignore` - Added frontend/dist, *.md exclusion with !frontend/README.md exception
- `.env.example` - 3 vars (POSTGRES_PASSWORD, RELOAD_TOKEN, REFRESH_CRON_HOUR), removed DOMAIN
- `.gitattributes` - Enforces LF line endings for *.sh files

## Decisions Made
- Added .gitattributes to enforce LF line endings for shell scripts -- prevents CRLF corruption when building Docker images from a Windows checkout

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added .gitattributes for LF line enforcement**
- **Found during:** Task 1 (docker/ directory files creation)
- **Issue:** Git on Windows auto-converts LF to CRLF, which would break docker/entrypoint.sh inside Docker containers (#!/bin/sh requires LF)
- **Fix:** Created .gitattributes with `*.sh text eol=lf` and re-normalized entrypoint.sh
- **Files modified:** .gitattributes
- **Verification:** `file docker/entrypoint.sh` reports "POSIX shell script, ASCII text executable"
- **Committed in:** 4c724a6

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for correctness on Windows development environments. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Docker infrastructure complete, ready for 06-03 VPS deployment guide
- `docker compose config` validates successfully
- All services defined with proper health checks and dependency ordering
- Frontend build pipeline containerized via multi-stage nginx.Dockerfile

## Self-Check: PASSED

- All 8 files verified present on disk
- All 3 task commits verified in git history (c0d73fb, 4c724a6, 04200b1)

---
*Phase: 06-pipeline-and-deployment*
*Completed: 2026-03-22*
