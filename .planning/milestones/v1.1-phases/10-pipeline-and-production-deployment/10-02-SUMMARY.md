---
phase: 10-pipeline-and-production-deployment
plan: 02
status: completed
duration: "~10min (including checkpoint approval)"
tasks_completed: 2
files_modified: 4
files_created: 2
requirements_satisfied: [PIPE-02, PIPE-03]
---

# Plan 10-02 Summary: Seed Script and Docker Infrastructure

## What Was Done

### Task 1: Seed Script + Docker Updates (TDD)

**scripts/seed_spread.py** (new):
- `seed_spread_predictions(season, dry_run)` seeds historical spread predictions for completed games
- Uses `model.predict(X)` (regression) NOT `predict_proba()` (classification)
- Computes `actual_spread = home_score - away_score` (home-team convention)
- Predicted winner follows home-team convention: `predicted_spread >= 0` -> home wins
- ON CONFLICT DO UPDATE on game_id for idempotency
- CLI: `python -m scripts.seed_spread --seasons 2023 2024 [--dry-run]`

**tests/test_seed_spread.py** (new, 3 tests):
- `test_seed_spread_predictions` - verifies regression inference (model.predict not predict_proba)
- `test_seed_spread_backfills_actuals` - verifies actual_spread sign convention (home minus away)
- `test_seed_spread_idempotent` - verifies ON CONFLICT DO UPDATE upsert pattern

**docker-compose.yml** (modified):
- Added SPREAD_MODEL_PATH and SPREAD_EXPERIMENTS_PATH to both api and worker services
- Both point to /app/models-vol/ volume paths

**docker/entrypoint.sh** (modified):
- Added separate spread artifact guard (if best_spread_model.json missing)
- Handles v1.0-to-v1.1 upgrade: classifier volume exists but spread artifacts missing
- Copies best_spread_model.json and spread_experiments.jsonl on first boot

### Task 2: Human Verification Checkpoint
- All 3 seed spread tests pass
- All 13 pipeline tests pass
- Import verification succeeds
- Docker env vars configured (2 services x 2 vars)
- Entrypoint guard verified (separate from classifier guard)
- User approved deploy readiness

## Verification Results

| Check | Result |
|-------|--------|
| test_seed_spread.py (3 tests) | PASS |
| test_pipeline.py (13 tests) | PASS |
| seed_spread import | OK |
| SPREAD_MODEL_PATH in docker-compose | 2 matches (api + worker) |
| best_spread_model in entrypoint.sh | 2 matches (guard + cp) |
| Full suite (excluding Postgres integration) | 83 passed |

## Key Decisions
- Mirrored classifier seed pattern (seed_predictions.py) for consistency
- Separate entrypoint guard handles v1.0-to-v1.1 upgrade path
- Default seasons [2023, 2024] match training validation + holdout years
