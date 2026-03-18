# Phase 6: Pipeline and Deployment - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Automate weekly data refresh and deploy the full stack via Docker Compose on a Linux VPS. The system runs five services (postgres, api, worker, mlflow, caddy) with a human approval gate before model deployment. Weekly pipeline ingests new data, recomputes features, stages a candidate model, and generates predictions with the current approved model.

</domain>

<decisions>
## Implementation Decisions

### Docker service architecture
- Single Dockerfile for the Python app, run as two services: `api` (uvicorn) and `worker` (APScheduler)
- Different entrypoints: `api` runs uvicorn, `worker` runs the scheduler loop
- Separate manual entry point (`pipeline.refresh`) for one-shot runs via `docker compose exec`
- MLflow runs as a dedicated service using the official `ghcr.io/mlflow/mlflow` image
- Caddy replaces nginx as the edge proxy (deviation from earlier planning docs that specified nginx — Caddy is strictly better for auto-SSL)
- Caddy serves `frontend/dist/` static files and proxies `/api/*` to the FastAPI container

### MLflow configuration
- MLflow server backed by PostgreSQL (separate `mlflow` database on the same postgres instance)
- `CREATE DATABASE mlflow;` added to `init.sql`
- Backend URI: `postgresql://nfl:${POSTGRES_PASSWORD}@postgres:5432/mlflow`
- Artifacts stored on the `mlartifacts` named volume
- MLflow stays internal-only — not publicly proxied through Caddy. Access via SSH tunnel (`ssh -L 5000:localhost:5000 vps`) when needed
- Port 5000 not exposed to host in production

### Named volumes
- `pgdata` — PostgreSQL data
- `mlartifacts` — MLflow model artifacts
- `models` — Shared model artifacts (best_model.json, experiments.jsonl). Mounted into both api and worker containers. Worker stages candidate models here; API reads via /model/reload
- `caddy_data` — Caddy SSL certificates and state (essential for cert persistence across rebuilds)
- Single writer principle: only the worker process writes to experiments.jsonl. API reads only. Prevents corruption.

### Health checks and startup ordering
- Native Docker Compose health checks with `depends_on: condition: service_healthy`
- Postgres: `pg_isready -U nfl` health check
- API: Python-based health check (`python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"`) — avoids curl dependency in slim images
- Dependency chain: postgres → api, postgres → mlflow, postgres → worker, api → caddy
- Worker has soft dependency on API (for /model/reload calls, but mostly writes to postgres and models volume directly)

### Weekly refresh pipeline
- APScheduler with CronTrigger inside the worker container
- Default schedule: Tuesday 6 AM UTC (midnight Central — runs while user is asleep in El Paso)
- Schedule configurable via `REFRESH_CRON_HOUR` env var without image rebuild
- Pipeline sequence:
  1. `ingest_new_data()` — fetch latest week with tenacity retries. Includes staleness check: verify Monday night's game results are present in fetched data before proceeding. If data hasn't updated yet, fail and retry.
  2. `recompute_features()` — rebuild game_features table
  3. `retrain_and_stage()` — train candidate model, write to models volume. **NON-FATAL**: if this step fails, log the error, skip staging, continue to step 4. Retraining is opportunistic; predictions are the deliverable.
  4. `generate_predictions()` — predict upcoming week with the CURRENT approved model (not the staged candidate). Always runs if steps 1-2 succeeded.
- Steps 1-2: strict stop-on-failure (each depends on prior step's output)
- Step 3: non-fatal failure — retraining failure doesn't block predictions
- Step 4: always runs if data is fresh
- On failure (post-retry): log error with step name + traceback, leave existing state untouched. Next scheduled run retries from step 1.
- Staged model does NOT go live automatically. Human calls POST /model/reload after inspecting metrics. This is the PIPE-03 approval gate.

### Secrets and environment management
- Single `.env` file at project root (gitignored) with actual secrets
- `.env.example` committed with placeholder values as template
- `POSTGRES_PASSWORD` is the single source for password — database URLs constructed in `docker-compose.yml` using `${POSTGRES_PASSWORD}` interpolation (Docker Compose supports this). Password lives in exactly one place.
- `.env` in `.gitignore` from day one

### SSL and edge proxy
- Caddy with automatic Let's Encrypt SSL certificate provisioning
- Zero manual cert management — Caddy handles issuance and renewal
- `caddy_data` volume persists certificates across container rebuilds (avoids Let's Encrypt rate limits)
- Caddyfile: serves frontend static files at root, proxies `/api/*` to `api:8000`

### VPS bootstrap sequence
1. Install Docker + Docker Compose on VPS
2. `git clone <repo>`
3. `cp .env.example .env` — fill in real `POSTGRES_PASSWORD`, `RELOAD_TOKEN`, domain name
4. Verify DNS is pointed at VPS IP (before compose up — Caddy needs DNS resolving to provision SSL cert)
5. `docker compose up -d` — postgres starts (init.sql creates both databases), MLflow connects, API loads model, Caddy provisions cert
6. First data run interactively: `docker compose exec worker python -m pipeline.refresh` — watch 20-season ingestion in real time (~30+ min). First run is special: 14M+ rows of play-by-play, full feature build, initial model training. Run interactively to catch failures, not backgrounded.

### Claude's Discretion
- Multi-stage Dockerfile optimization (build vs runtime layers)
- Exact Caddy container image version
- Log format and log rotation strategy
- Worker process management (signal handling, graceful shutdown)
- APScheduler job store configuration (in-memory vs PostgreSQL-backed)
- Exact tenacity retry parameters (count, backoff, jitter)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Docker setup
- `docker-compose.yml` — Current compose file (postgres only — must be expanded to all services)
- `sql/init.sql` — Database schema DDL (needs `CREATE DATABASE mlflow;` added)

### API and model interfaces
- `api/main.py` — FastAPI app with lifespan model loading, CORS config
- `api/config.py` — Settings class (env vars: DATABASE_URL, MODEL_PATH, EXPERIMENTS_PATH, RELOAD_TOKEN, confidence thresholds, CORS origins)
- `api/routes/` — All API routes including health check endpoint
- `models/predict.py` — Prediction pipeline: `load_best_model()`, `get_best_experiment()`, `detect_current_week()`, `generate_predictions()`
- `models/train.py` — Training pipeline (worker reuses for retraining)
- `models/artifacts/` — Best model checkpoint location (shared volume mount point)
- `models/experiments.jsonl` — Experiment log (shared volume, single writer)

### Data and feature pipeline
- `data/sources.py` — Data ingestion with team abbreviation constants
- `data/db.py` — SQLAlchemy engine via `get_engine()` + `get_table()`
- `features/build.py` — Feature computation pipeline (`build_game_features()`)

### Frontend
- `frontend/dist/` — Built React dashboard (Caddy serves this directory)
- `frontend/package.json` — Frontend build configuration

### Phase 4 context
- `.planning/phases/04-prediction-api/04-CONTEXT.md` — API design decisions: confidence tiers, current week detection, reload token protection, experiments endpoint reads jsonl directly

### Project rules
- `CLAUDE.md` — Critical rules: forbidden features, temporal split, experiment loop constraints
- `.planning/REQUIREMENTS.md` — PIPE-01 through PIPE-04 requirements

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `models/predict.py`: `generate_predictions()` and `detect_current_week()` — pipeline step 4 calls these directly
- `data/sources.py`: ingestion functions with tenacity retries already in place — pipeline step 1 wraps these
- `features/build.py`: `build_game_features()` — pipeline step 2 calls this
- `models/train.py`: training pipeline — pipeline step 3 reuses this for retraining
- `api/config.py`: `get_confidence_tier()` — needed by `generate_predictions()`

### Established Patterns
- Database access via `DATABASE_URL` env var + dotenv
- Model artifacts in `models/artifacts/` directory
- Dual logging: experiments.jsonl (flat file) + MLflow
- Dependencies in `pyproject.toml` (tenacity, APScheduler to be added)
- POST /model/reload with X-Reload-Token header for human approval gate

### Integration Points
- `docker-compose.yml` — currently postgres-only, must be expanded to 5 services
- `sql/init.sql` — needs `CREATE DATABASE mlflow;` for MLflow backend
- Worker imports from `data.sources`, `features.build`, `models.train`, `models.predict`
- Shared `models` volume: worker writes candidate models, API reads on reload
- API health check at GET /api/health — used by Docker health checks and Caddy dependency

</code_context>

<specifics>
## Specific Ideas

- Caddy over nginx for zero-config SSL — deviation from earlier planning docs, update them accordingly
- MLflow internal-only with SSH tunnel access — keeps attack surface minimal
- Staleness check in ingestion: verify Monday night's game results are in fetched data before proceeding
- Step 3 (retrain) is non-fatal: predictions are the weekly deliverable, retraining is opportunistic
- First VPS deployment run interactively to watch 20-season ingestion in real time
- Password in one place: construct database URLs from `${POSTGRES_PASSWORD}` in docker-compose.yml

</specifics>

<deferred>
## Deferred Ideas

- Notification on pipeline failure (email, Slack, etc.) — useful but out of scope for v1
- CI/CD pipeline with pre-built images on a registry — over-engineering for a single-VPS project that deploys twice a year
- Monitoring/alerting (Prometheus, Grafana) — nice to have but not v1 scope
- Automatic model comparison (staged vs current) with metrics diff before reload — could be a v2 enhancement

</deferred>

---

*Phase: 06-pipeline-and-deployment*
*Context gathered: 2026-03-17*
