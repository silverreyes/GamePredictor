# Phase 10: Pipeline and Production Deployment - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Spread predictions are generated automatically each week alongside classifier predictions, historical spread predictions are seeded for 2023-2024, and the complete v1.1 system is deployed to production at nostradamus.silverreyes.net. No model retraining changes — spread uses inference only.

</domain>

<decisions>
## Implementation Decisions

### Pipeline spread step
- Add spread inference as a **new step 5** in `run_pipeline()`, separate from classifier prediction step 4
- Step 5 is **non-fatal**: if spread inference fails, classifier predictions from step 4 are still valid; error is logged and pipeline continues
- Loads spread model via `load_best_spread_model()` and calls `generate_spread_predictions()` for the current week
- **Manual reload gate preserved**: pipeline generates and stores predictions in DB, but does NOT call POST /model/reload — human triggers reload to go live (matches existing Phase 6 approval pattern)
- Add **SPREAD_MODEL_PATH** and **SPREAD_EXPERIMENTS_PATH** env vars to the worker service in docker-compose.yml (mirrors API service config from Phase 8)

### Historical seeding
- **Standalone script**: new `scripts/seed_spread.py` — run once manually before deploy
- **Seeds 2023 + 2024 seasons**: both are in the database from Phase 1 ingestion; weekly pipeline handles 2025+ going forward
- **Backfills actual results**: seed script populates predicted_spread, predicted_winner AND actual_spread, actual_winner, correct for completed games — dashboard shows accuracy metrics immediately on first deploy
- **Idempotent with upsert**: uses ON CONFLICT DO UPDATE (same pattern as `generate_spread_predictions()`) — safe to re-run without duplicates

### Deploy mechanics (Claude's Discretion)
- Entrypoint.sh extended to seed `best_spread_model.json` and `spread_experiments.jsonl` alongside classifier artifacts
- Docker volume and env var configuration for spread model paths
- Caddy/nginx config changes if needed (likely none — existing reverse proxy covers /api/* routes)
- Any build/deploy steps for the VPS

### Claude's Discretion
- Exact step 5 function signature and error handling details
- Seed script CLI arguments (if any) vs hardcoded season list
- Order of operations in entrypoint.sh for spread artifact seeding
- Whether to add logging or progress output to seed script

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — PIPE-01, PIPE-02, PIPE-03 define all Phase 10 requirements
- `.planning/ROADMAP.md` §Phase 10 — Success criteria (3 items)

### Existing pipeline (modify this)
- `pipeline/refresh.py` — `run_pipeline()` orchestrator: add step 5 for spread inference
- `pipeline/worker.py` — APScheduler worker, runs `run_pipeline()` every Tuesday 06:00 UTC

### Spread inference functions (call these)
- `models/predict.py` — `load_best_spread_model()`, `get_best_spread_experiment()`, `generate_spread_predictions()` — all built in Phase 8
- `models/predict.py:detect_current_week()` — Used by step 4, reuse in step 5 for offseason guard

### Docker/deploy infrastructure
- `docker-compose.yml` — Worker service needs SPREAD_MODEL_PATH and SPREAD_EXPERIMENTS_PATH env vars
- `docker/entrypoint.sh` — Seed spread model artifacts alongside classifier on first boot
- `Dockerfile` — May need no changes (artifacts already COPY'd via `COPY . .`)

### Prior phase context
- `.planning/phases/08-database-and-api-integration/08-CONTEXT.md` — Spread inference patterns, env var naming conventions, API config decisions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `models/predict.py:generate_spread_predictions()` — Full spread inference pipeline: build features, get rolling stats, run regression, upsert to spread_predictions table
- `models/predict.py:load_best_spread_model()` — Loads XGBRegressor from JSON artifact
- `models/predict.py:get_best_spread_experiment()` — Parses spread_experiments.jsonl for best kept experiment (lowest MAE)
- `models/predict.py:detect_current_week()` — Offseason guard, returns (season, week) or None
- `pipeline/refresh.py:generate_current_predictions()` — Pattern for step 5 (load model, get experiment, detect week, generate)

### Established Patterns
- Pipeline steps are try/except with fatal vs non-fatal classification — step 5 follows non-fatal pattern (matches step 3)
- Entrypoint.sh seeds model volume on first boot with simple cp commands
- Docker Compose env vars follow UPPER_SNAKE_CASE convention
- Standalone scripts live in project root or dedicated directories (train_spread.py is in models/)

### Integration Points
- `pipeline/refresh.py:run_pipeline()` — Add step 5 after step 4
- `docker-compose.yml` worker service — Add spread env vars
- `docker/entrypoint.sh` — Add spread artifact seeding
- New `scripts/seed_spread.py` — Standalone seed script (new file)

</code_context>

<specifics>
## Specific Ideas

- Seed script seeds predictions for completed games only (games with scores in schedules table), skipping unplayed games
- The spread model (Exp 1) was trained on 2005-2022, so 2023+2024 predictions are genuine out-of-sample
- Training temporal split (2005-2022 train, 2023 val, 2024 holdout) is NOT changed — this is inference only

</specifics>

<deferred>
## Deferred Ideas

- Retraining with 2023 in training set and shifting validation to 2024 / holdout to 2025 — future milestone
- 2025 season data ingestion and seeding — handled naturally by weekly pipeline once deployed
- Over/under totals model — deferred to v1.2

</deferred>

---

*Phase: 10-pipeline-and-production-deployment*
*Context gathered: 2026-03-23*
