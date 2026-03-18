---
phase: 06-pipeline-and-deployment
verified: 2026-03-17T00:00:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 6: Pipeline and Deployment Verification Report

**Phase Goal:** The full system runs in Docker Compose on a Linux VPS with automated weekly data refresh and a human approval gate before model deployment
**Verified:** 2026-03-17
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

The phase has 9 must-have truths drawn from the two plan frontmatter blocks.

| #  | Truth                                                                                       | Status     | Evidence                                                                                    |
|----|---------------------------------------------------------------------------------------------|-----------|---------------------------------------------------------------------------------------------|
| 1  | Weekly refresh ingests new data, recomputes features, stages a candidate model, and generates predictions | ✓ VERIFIED | `run_pipeline()` in refresh.py executes all 4 steps in order with explicit logging         |
| 2  | Retraining failure does not block prediction generation                                      | ✓ VERIFIED | Step 3 wrapped in try/except; `logger.exception("Step 3 FAILED (non-fatal): retrain_and_stage -- continuing to predictions")` — step 4 still executes |
| 3  | Staleness check prevents pipeline from proceeding with stale data                           | ✓ VERIFIED | `ingest_new_data` queries `MAX(week)` before and after, raises `ValueError("Data stale: ...")` if week_after <= week_before |
| 4  | APScheduler runs on Tuesday 6 AM UTC with configurable hour                                 | ✓ VERIFIED | `CronTrigger(day_of_week="tue", hour=cron_hour, timezone="UTC")` in worker.py; `REFRESH_CRON_HOUR` env var with default `"6"` |
| 5  | Staged model does not go live until POST /model/reload is called                             | ✓ VERIFIED | `save_best_model` saves to `model_dir` volume; log message explicitly states "call POST /model/reload to go live"; API loads model only on `/api/model/reload` call |
| 6  | docker compose config validates without errors                                               | ✓ VERIFIED | `docker compose config --quiet` exits 0 (verified live)                                    |
| 7  | Docker Compose defines 5 services: postgres, api, mlflow, worker, caddy                     | ✓ VERIFIED | Exactly 5 services confirmed; `grep -c` returns 5                                          |
| 8  | API container reads model artifacts from shared models volume (read-only)                   | ✓ VERIFIED | `models:/app/models-vol:ro` in api service volumes                                         |
| 9  | Worker container writes model artifacts to shared models volume (read-write)                | ✓ VERIFIED | `models:/app/models-vol` (no `:ro`) in worker service volumes                              |

Additional truths from plan 02 must_haves — all verified:

| #  | Truth                                                                        | Status     | Evidence                                                      |
|----|------------------------------------------------------------------------------|------------|---------------------------------------------------------------|
| 10 | Caddy serves frontend static files at root and proxies /api/* to api:8000   | ✓ VERIFIED | `reverse_proxy api:8000` and `try_files {path} /index.html` in Caddyfile |
| 11 | MLflow is internal-only (no port exposed to host in production compose)      | ✓ VERIFIED | Only `postgres` (5432) and `caddy` (80/443) expose ports; mlflow section has no `ports:` key |
| 12 | Data and model artifacts persist across container rebuilds via named volumes | ✓ VERIFIED | 4 named volumes defined: pgdata, mlartifacts, models, caddy_data |
| 13 | Frontend API calls use relative URLs (/api/...) not localhost                | ✓ VERIFIED | `const API_BASE = import.meta.env.VITE_API_URL ?? ""` in frontend/src/lib/api.ts |
| 14 | .env.example has all required env vars with placeholder values               | ✓ VERIFIED | POSTGRES_PASSWORD, RELOAD_TOKEN, DOMAIN, REFRESH_CRON_HOUR all present |

**Score:** 9/9 primary truths verified (14/14 including full plan 02 truth set)

### Required Artifacts

| Artifact                      | Expected                                              | Status     | Details                                                                             |
|-------------------------------|-------------------------------------------------------|------------|-------------------------------------------------------------------------------------|
| `pipeline/__init__.py`        | Package init                                          | ✓ VERIFIED | Exists, 0 bytes (correct empty package marker)                                     |
| `pipeline/refresh.py`         | Four-step pipeline orchestration with mixed failure modes | ✓ VERIFIED | 334 lines; exports run_pipeline, ingest_new_data, recompute_features, retrain_and_stage, generate_current_predictions |
| `pipeline/worker.py`          | APScheduler entrypoint with SIGTERM handler           | ✓ VERIFIED | 40 lines; BlockingScheduler, CronTrigger, SIGTERM/SIGINT handlers, configurable cron hour |
| `tests/test_pipeline.py`      | Unit tests for pipeline steps, failure modes, worker  | ✓ VERIFIED | 358 lines; 10 tests, all passing                                                    |
| `Dockerfile`                  | Multi-stage Python image for api and worker services  | ✓ VERIFIED | Multi-stage (builder + runtime); `FROM python:3.11-slim` both stages; CMD present  |
| `mlflow.Dockerfile`           | Custom MLflow image with psycopg2-binary              | ✓ VERIFIED | `FROM ghcr.io/mlflow/mlflow:2.21.3`; `psycopg2-binary` installed; version pinned  |
| `Caddyfile`                   | Edge proxy config for static files + API reverse proxy | ✓ VERIFIED | `reverse_proxy api:8000`, `try_files {path} /index.html`, `{$DOMAIN:localhost}`    |
| `docker-compose.yml`          | Full 5-service orchestration with health checks        | ✓ VERIFIED | 5 services; 4 `service_healthy` conditions; named volumes; correct dependency chain |
| `.env.example`                | Template for environment variables                    | ✓ VERIFIED | All 4 required env vars present with placeholder values                            |
| `sql/00-create-mlflow-db.sh`  | MLflow database creation on first postgres boot       | ✓ VERIFIED | `#!/bin/bash`; `CREATE DATABASE mlflow OWNER $POSTGRES_USER`                       |

### Key Link Verification

#### Plan 01 Key Links

| From                     | To                   | Via                                               | Status     | Detail                                                                 |
|--------------------------|----------------------|---------------------------------------------------|------------|------------------------------------------------------------------------|
| `pipeline/refresh.py`    | `data/ingest.py`     | ingest_new_data calls ingest logic                | ✓ WIRED    | `from data.db import`, `from data.ingest import`, `from data.loaders import`, `from data.transforms import`, `from data.validators import` all present at module level |
| `pipeline/refresh.py`    | `features/build.py`  | recompute_features calls build_game_features + store | ✓ WIRED | `from features.build import build_game_features, store_game_features` inside recompute_features body; also used in retrain_and_stage |
| `pipeline/refresh.py`    | `models/train.py`    | retrain_and_stage reuses training pipeline        | ✓ WIRED    | `from models.train import DEFAULT_PARAMS, load_and_split, log_experiment, save_best_model, setup_mlflow, should_keep, train_and_evaluate` inside function body |
| `pipeline/refresh.py`    | `models/predict.py`  | generate_current_predictions calls generate_predictions | ✓ WIRED | `from models.predict import detect_current_week, generate_predictions, get_best_experiment, load_best_model` inside function body |
| `pipeline/worker.py`     | `pipeline/refresh.py` | APScheduler job calls run_pipeline               | ✓ WIRED    | `from pipeline.refresh import run_pipeline` at module level; passed to `scheduler.add_job(run_pipeline, ...)` |

#### Plan 02 Key Links

| From                 | To                    | Via                                          | Status     | Detail                                                      |
|----------------------|-----------------------|----------------------------------------------|------------|-------------------------------------------------------------|
| `docker-compose.yml` | `Dockerfile`          | build context for api and worker services    | ✓ WIRED    | `build: .` appears for both api (line 20) and worker (line 40) |
| `docker-compose.yml` | `mlflow.Dockerfile`   | build context for mlflow service             | ✓ WIRED    | `dockerfile: mlflow.Dockerfile` in mlflow service build block |
| `docker-compose.yml` | `Caddyfile`           | volume mount into caddy container            | ✓ WIRED    | `./Caddyfile:/etc/caddy/Caddyfile` in caddy volumes         |
| `docker-compose.yml` | `sql directory`       | postgres init script mount                   | ✓ WIRED    | `./sql:/docker-entrypoint-initdb.d` in postgres volumes     |
| `caddy`              | `api`                 | reverse_proxy for /api/* requests            | ✓ WIRED    | `reverse_proxy api:8000` in Caddyfile handle block          |
| `worker`             | `models volume`       | read-write mount for staging candidate models | ✓ WIRED   | `models:/app/models-vol` (no `:ro`) in worker volumes       |
| `api`                | `models volume`       | read-only mount for serving models           | ✓ WIRED    | `models:/app/models-vol:ro` in api volumes                  |

### Requirements Coverage

| Requirement | Source Plan | Description                                                                               | Status      | Evidence                                                                                   |
|-------------|------------|-------------------------------------------------------------------------------------------|-------------|--------------------------------------------------------------------------------------------|
| PIPE-01     | 06-01-PLAN | Weekly refresh automatically fetches new game data and recomputes features on a schedule   | ✓ SATISFIED | `ingest_new_data` + `recompute_features` steps in `run_pipeline`; APScheduler CronTrigger Tuesday 6 AM UTC in `worker.py` |
| PIPE-02     | 06-01-PLAN | Weekly refresh automatically retrains and stages a candidate model — staged only, not live | ✓ SATISFIED | `retrain_and_stage` saves to `model_dir` volume only; explicit log "call POST /model/reload to go live" |
| PIPE-03     | 06-01-PLAN, 06-02-PLAN | New model staged but not live until POST /model/reload is called manually | ✓ SATISFIED | Model file written to shared volume read-only for API; API hot-swap only on explicit reload endpoint call |
| PIPE-04     | 06-02-PLAN | Full stack runs under Docker Compose: postgres, api, mlflow, frontend, worker services     | ✓ SATISFIED | docker-compose.yml defines all 5 services with health checks, named volumes, Caddy proxy  |

All 4 PIPE requirements satisfied. No orphaned requirements — REQUIREMENTS.md maps exactly PIPE-01 through PIPE-04 to Phase 6 and all are covered by these two plans.

### Anti-Patterns Found

No anti-patterns found in any phase 6 files. Scan of pipeline/refresh.py, pipeline/worker.py, docker-compose.yml, Dockerfile, and Caddyfile returned no TODO/FIXME/placeholder markers, empty implementations, or stub handlers.

One noted deviation (not a blocker): The Dockerfile has a default `CMD ["uvicorn", "api.main:app", ...]` which was added during a bug fix (Plan 02 deviation c362756). The docker-compose.yml overrides this CMD per-service, so both api and worker use correct entrypoints. This is correct behavior, not a stub.

### Human Verification Required

The following items require runtime or visual confirmation that automated static analysis cannot provide:

**1. Full stack boot with docker compose up**

Test: Copy .env.example to .env, populate real credentials, run `docker compose up -d`, then check `docker compose ps`
Expected: All 5 services show "Up" (healthy) status — postgres, api, worker, mlflow, caddy
Why human: Static config validation passes but actual container startup, network resolution between services, and health check timing require a live Docker environment

**2. End-to-end weekly refresh execution**

Test: Exec into the worker container and trigger `run_pipeline()` manually (or wait for Tuesday cron trigger); observe logs for all 4 steps
Expected: Steps 1-4 log progress; no unhandled exceptions; predictions table updated after step 4
Why human: Requires live PostgreSQL with data, nfl-data-py network access, and MLflow server — not reproducible via unit tests

**3. Human approval gate (PIPE-03 runtime verification)**

Test: After worker stages a new model (step 3), verify the API is still serving the old model; then call POST /api/model/reload and verify the new model is now active
Expected: Staged model file exists on disk but GET /api/model/info still shows old version until reload is called
Why human: Requires live stack with a completed retrain cycle; cannot be verified statically

**4. Caddy TLS and SPA routing**

Test: Navigate to `https://{domain}/` — dashboard loads; navigate to `/experiments` directly (not from nav link) — dashboard loads (not 404)
Expected: Caddy serves correct SPA with HTTPS certificate; try_files fallback routes all paths to index.html
Why human: Requires DNS + domain configuration and live Caddy container with SSL provisioning

### Gaps Summary

No gaps. All automated checks passed:

- All 9 must-have truths from plan frontmatter: verified
- All 10 required artifacts: exist, substantive, and wired
- All 12 key links: verified present in actual code
- All 4 requirements (PIPE-01 through PIPE-04): satisfied with implementation evidence
- All 10 unit tests: passing
- `docker compose config --quiet`: exits 0
- All pipeline functions: importable without errors
- No anti-patterns detected

The 4 human verification items above are operational concerns (live Docker environment, network, DNS) that cannot be verified by static analysis. They do not represent code gaps — the code is complete and correctly wired.

---

_Verified: 2026-03-17_
_Verifier: Claude (gsd-verifier)_
