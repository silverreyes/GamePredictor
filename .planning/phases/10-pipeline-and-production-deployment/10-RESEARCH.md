# Phase 10: Pipeline and Production Deployment - Research

**Researched:** 2026-03-23
**Domain:** Pipeline orchestration, Docker deployment, data seeding
**Confidence:** HIGH

## Summary

Phase 10 is the final phase of v1.1. It has three concrete deliverables: (1) add spread inference as step 5 in the existing weekly pipeline, (2) create a seed script that backfills historical spread predictions for 2023+2024, and (3) deploy all v1.1 changes to production. All three are well-constrained integration tasks with established patterns to follow from v1.0 and prior v1.1 phases.

The codebase already contains every function needed for spread inference (`load_best_spread_model()`, `get_best_spread_experiment()`, `generate_spread_predictions()` in `models/predict.py`), an existing seed script pattern (`scripts/seed_predictions.py` for classifier predictions), a working Docker setup (`docker-compose.yml`, `docker/entrypoint.sh`, `Dockerfile`), and comprehensive pipeline orchestration (`pipeline/refresh.py`). This phase is pure wiring -- no new algorithms, no new libraries, no schema changes.

**Primary recommendation:** Follow the existing patterns exactly. Step 5 mirrors step 4's structure. The spread seed script mirrors `scripts/seed_predictions.py`. Docker changes are additive env vars and artifact seeding.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Add spread inference as a **new step 5** in `run_pipeline()`, separate from classifier prediction step 4
- Step 5 is **non-fatal**: if spread inference fails, classifier predictions from step 4 are still valid; error is logged and pipeline continues
- Loads spread model via `load_best_spread_model()` and calls `generate_spread_predictions()` for the current week
- **Manual reload gate preserved**: pipeline generates and stores predictions in DB, but does NOT call POST /model/reload -- human triggers reload to go live (matches existing Phase 6 approval pattern)
- Add **SPREAD_MODEL_PATH** and **SPREAD_EXPERIMENTS_PATH** env vars to the worker service in docker-compose.yml (mirrors API service config from Phase 8)
- **Standalone script**: new `scripts/seed_spread.py` -- run once manually before deploy
- **Seeds 2023 + 2024 seasons**: both are in the database from Phase 1 ingestion; weekly pipeline handles 2025+ going forward
- **Backfills actual results**: seed script populates predicted_spread, predicted_winner AND actual_spread, actual_winner, correct for completed games -- dashboard shows accuracy metrics immediately on first deploy
- **Idempotent with upsert**: uses ON CONFLICT DO UPDATE (same pattern as `generate_spread_predictions()`) -- safe to re-run without duplicates
- Entrypoint.sh extended to seed `best_spread_model.json` and `spread_experiments.jsonl` alongside classifier artifacts
- Docker volume and env var configuration for spread model paths

### Claude's Discretion
- Exact step 5 function signature and error handling details
- Seed script CLI arguments (if any) vs hardcoded season list
- Order of operations in entrypoint.sh for spread artifact seeding
- Whether to add logging or progress output to seed script
- Caddy/nginx config changes if needed (likely none -- existing reverse proxy covers /api/* routes)
- Any build/deploy steps for the VPS

### Deferred Ideas (OUT OF SCOPE)
- Retraining with 2023 in training set and shifting validation to 2024 / holdout to 2025 -- future milestone
- 2025 season data ingestion and seeding -- handled naturally by weekly pipeline once deployed
- Over/under totals model -- deferred to v1.2
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PIPE-01 | Weekly pipeline generates spread predictions (inference only, no retrain) for current week alongside classifier predictions | Step 5 in `run_pipeline()` calling existing `generate_spread_predictions()` with offseason guard via `detect_current_week()` |
| PIPE-02 | Seed script generates historical spread predictions for completed games (2023 validation season) | New `scripts/seed_spread.py` mirroring `scripts/seed_predictions.py` pattern, extended to seed 2023+2024 with actual results backfill |
| PIPE-03 | All changes deployed to production VPS at nostradamus.silverreyes.net | Docker compose updates (env vars), entrypoint.sh spread artifact seeding, frontend rebuild, deploy |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| xgboost | >=3.2.0 | Spread model inference (XGBRegressor) | Already in pyproject.toml, used by existing spread functions |
| sqlalchemy | >=2.0 | PostgreSQL upsert via `pg_insert` | Already used by `generate_spread_predictions()` |
| pandas | >=2.0 | Feature matrix building, SQL queries | Already used throughout pipeline |
| APScheduler | >=3.10,<4.0 | Weekly pipeline scheduling (worker) | Already used by `pipeline/worker.py` |
| fastapi | >=0.115.0 | API serving (no changes needed) | Already running, spread endpoints exist |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| argparse | stdlib | Seed script CLI arguments | For `--season` and `--dry-run` flags |
| logging | stdlib | Pipeline step logging | For step 5 log messages |

### Alternatives Considered
None. This phase uses only existing project dependencies. No new packages needed.

**Installation:**
```bash
# No new packages needed -- all dependencies already in pyproject.toml
```

## Architecture Patterns

### Recommended Project Structure
```
pipeline/
  refresh.py          # ADD step 5 (generate_spread_predictions call)
  worker.py           # NO CHANGES (already runs run_pipeline())
scripts/
  seed_predictions.py # EXISTING (classifier seed -- pattern to follow)
  seed_spread.py      # NEW (spread seed script)
docker/
  entrypoint.sh       # MODIFY (add spread artifact seeding)
docker-compose.yml    # MODIFY (add spread env vars to worker)
```

### Pattern 1: Non-Fatal Pipeline Step (Step 5)

**What:** Add spread inference step that mirrors step 4 but is non-fatal (matches step 3 pattern).
**When to use:** When a pipeline step's failure should not prevent other steps from completing.
**Example:**
```python
# Source: pipeline/refresh.py (existing step 3 pattern)
def generate_current_spread_predictions(engine, spread_model_path, spread_experiments_path):
    """Step 5: Generate spread predictions for the current week.

    Non-fatal: if this step fails, classifier predictions from step 4
    are still valid and the pipeline continues.
    """
    from models.predict import (
        detect_current_week,
        generate_spread_predictions,
        get_best_spread_experiment,
        load_best_spread_model,
    )

    # Load spread model
    spread_model = load_best_spread_model(spread_model_path)

    # Get best spread experiment for model_id
    best_exp = get_best_spread_experiment(spread_experiments_path)
    model_id = best_exp["experiment_id"] if best_exp else None

    # Detect current week (reuse same function as step 4)
    current = detect_current_week(engine)
    if current is None:
        logger.info("Offseason detected -- skipping spread prediction generation")
        return

    season, week = current
    logger.info("Generating spread predictions for season %d, week %d...", season, week)

    predictions = generate_spread_predictions(
        spread_model, season, week, engine, model_id=model_id,
    )
    logger.info("Generated %d spread predictions", len(predictions))
```

**In run_pipeline():**
```python
# Step 5: Generate spread predictions (non-fatal)
try:
    generate_current_spread_predictions(engine, spread_model_path, spread_experiments_path)
except Exception:
    logger.exception("Step 5 FAILED (non-fatal): generate_current_spread_predictions -- continuing")
```

### Pattern 2: Historical Seed Script (seed_spread.py)

**What:** Standalone script that generates spread predictions for completed historical games and backfills actual results.
**When to use:** Once before first production deploy to populate dashboard with historical data.
**Example approach:**
```python
# Source: scripts/seed_predictions.py (existing classifier seed pattern)
# Key difference: spread uses model.predict() not model.predict_proba()
# Key difference: must compute actual_spread from home_score - away_score
# Key difference: must support seeding multiple seasons (2023 + 2024)
# Key difference: uses spread_predictions table, not predictions table

def seed_spread_predictions(season: int, dry_run: bool = False) -> int:
    """Generate spread predictions for all completed games in a season.

    Unlike generate_spread_predictions() (targets unplayed games),
    this targets completed games where actual outcomes are known.
    Populates both predicted AND actual columns.
    """
    # Load spread model + experiment info
    # Build features for target season
    # Filter to completed games with rolling features
    # Run model.predict() to get predicted spreads
    # Compute actuals: actual_spread = home_score - away_score
    # Determine actual_winner and correct flag
    # Upsert into spread_predictions table
```

### Pattern 3: Entrypoint Artifact Seeding

**What:** Copy spread model artifacts to volume on first boot.
**When to use:** Docker entrypoint for volume initialization.
**Example:**
```bash
# Source: docker/entrypoint.sh (existing pattern)
#!/bin/sh
MODEL_VOL="/app/models-vol"
if [ ! -f "$MODEL_VOL/best_model.json" ]; then
    echo "[entrypoint] Seeding models volume from image..."
    cp /app/models/artifacts/best_model.json "$MODEL_VOL/"
    cp /app/models/experiments.jsonl "$MODEL_VOL/"
    # NEW: seed spread artifacts
    cp /app/models/artifacts/best_spread_model.json "$MODEL_VOL/"
    cp /app/models/spread_experiments.jsonl "$MODEL_VOL/"
    echo "[entrypoint] Seeding complete."
fi
exec "$@"
```

### Pattern 4: Docker Compose Env Vars

**What:** Add spread model paths to worker service environment.
**When to use:** Worker service needs to know where spread model artifacts are.
**Example:**
```yaml
# Source: docker-compose.yml (existing pattern for classifier env vars)
worker:
  environment:
    # ... existing vars ...
    SPREAD_MODEL_PATH: /app/models-vol/best_spread_model.json
    SPREAD_EXPERIMENTS_PATH: /app/models-vol/spread_experiments.jsonl
```

### Anti-Patterns to Avoid
- **Calling POST /model/reload from pipeline:** The manual reload gate is a locked decision. Pipeline stores predictions in DB only; human triggers reload.
- **Skipping offseason guard in step 5:** Reuse `detect_current_week()` -- if it returns None, skip spread predictions. Step 4 already does this.
- **Creating a separate pipeline function for feature building:** `generate_spread_predictions()` already calls `build_game_features()` internally. Do NOT duplicate this logic in the pipeline step.
- **Modifying the entrypoint.sh guard condition:** The `if [ ! -f "$MODEL_VOL/best_model.json" ]` check should remain as-is. Spread artifacts are seeded alongside classifier artifacts inside the same block. Do NOT add a separate guard for spread files.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Spread inference | Custom regression logic | `generate_spread_predictions()` from `models/predict.py` | Already handles feature building, rolling stats lookup, upsert |
| Spread model loading | Custom deserialization | `load_best_spread_model()` from `models/predict.py` | Already handles path validation, XGBRegressor loading |
| Experiment lookup | Custom JSONL parsing | `get_best_spread_experiment()` from `models/predict.py` | Already handles keep flag, lowest MAE selection, path normalization |
| Current week detection | Hardcoded week logic | `detect_current_week()` from `models/predict.py` | Already handles offseason detection, data-driven week inference |
| Upsert logic | Manual INSERT/UPDATE | `pg_insert().on_conflict_do_update()` | Already used by `generate_spread_predictions()` and `seed_predictions.py` |

**Key insight:** Phase 8 already built all the spread inference functions. Phase 10 only needs to call them from new entry points (pipeline step 5 and seed script).

## Common Pitfalls

### Pitfall 1: Forgetting Env Vars in run_pipeline()
**What goes wrong:** Step 5 reads `SPREAD_MODEL_PATH` and `SPREAD_EXPERIMENTS_PATH` from env vars, but `run_pipeline()` only reads `MODEL_PATH` and `EXPERIMENTS_PATH` currently.
**Why it happens:** Easy to forget to add env var reads when adding a new step.
**How to avoid:** Add env var reads at the top of `run_pipeline()` alongside existing vars. Use same default paths as `api/config.py`.
**Warning signs:** Step 5 always looks for spread model at the default `models/artifacts/` path instead of the volume-mounted path.

### Pitfall 2: Seed Script Computing Actuals Incorrectly
**What goes wrong:** `actual_spread` should be `home_score - away_score` (positive means home won by X, matching the prediction convention). Getting the sign wrong means accuracy metrics are inverted.
**Why it happens:** Confusion about home vs away perspective for spread.
**How to avoid:** Use same convention as the `schedules.result` column: `home_score - away_score`. The spread model predicts home point differential, so actual_spread should be the actual home point differential.
**Warning signs:** `actual_winner` doesn't match what `correct` flag says.

### Pitfall 3: Seed Script Missing Actual Outcomes
**What goes wrong:** Seed script queries `home_score IS NULL` games (unplayed) instead of `home_score IS NOT NULL` games (completed).
**Why it happens:** Copy-pasting from `generate_spread_predictions()` which deliberately targets unplayed games.
**How to avoid:** The seed script should query completed games: `WHERE home_score IS NOT NULL`. The classifier seed script (`scripts/seed_predictions.py`) handles this by filtering `features_df.dropna(subset=["home_win"])`.
**Warning signs:** Empty predictions table after seeding, or predictions without actual results.

### Pitfall 4: Entrypoint Race Condition on Existing Volume
**What goes wrong:** If the models volume already has `best_model.json` (from v1.0 deploy), the entrypoint guard `if [ ! -f "$MODEL_VOL/best_model.json" ]` skips ALL seeding -- including spread artifacts that don't exist yet.
**Why it happens:** The guard checks for classifier model existence but spread model wasn't deployed in v1.0.
**How to avoid:** Add a separate guard for spread artifacts OR add spread seeding outside the existing guard. Recommended: add a second `if [ ! -f "$MODEL_VOL/best_spread_model.json" ]` block specifically for spread artifacts.
**Warning signs:** Spread model endpoints return 503 after deploy despite artifacts being in the Docker image.

### Pitfall 5: Windows Path Separators in JSONL
**What goes wrong:** Spread experiments logged on Windows have backslash paths that break on Linux Docker.
**Why it happens:** Python's `os.path.join()` on Windows produces backslashes.
**How to avoid:** `get_best_spread_experiment()` already normalizes paths with `.replace("\\", "/")`. Verify the pipeline step passes the normalized path to `load_best_spread_model()`.
**Warning signs:** `FileNotFoundError` for spread model in Docker despite file existing.

## Code Examples

Verified patterns from the existing codebase:

### Step 4 Pattern (to mirror for step 5)
```python
# Source: pipeline/refresh.py:generate_current_predictions (lines 243-276)
def generate_current_predictions(engine, model_path, experiments_path):
    """Step 4: Generate predictions for the current week."""
    from models.predict import (
        detect_current_week,
        generate_predictions,
        get_best_experiment,
        load_best_model,
    )
    model = load_best_model(model_path)
    best_exp = get_best_experiment(experiments_path)
    model_id = best_exp["experiment_id"] if best_exp else None
    current = detect_current_week(engine)
    if current is None:
        logger.info("Offseason detected -- skipping prediction generation")
        return
    season, week = current
    predictions = generate_predictions(
        model, season, week, engine, get_confidence_tier, model_id=model_id,
    )
    logger.info("Generated %d predictions", len(predictions))
```

### Non-Fatal Step Pattern (from step 3)
```python
# Source: pipeline/refresh.py:run_pipeline (lines 311-315)
# Step 3: Retrain (non-fatal)
try:
    retrain_and_stage(engine, experiments_path, model_dir)
except Exception:
    logger.exception("Step 3 FAILED (non-fatal): retrain_and_stage -- continuing to predictions")
```

### Classifier Seed Script Upsert Pattern
```python
# Source: scripts/seed_predictions.py (lines 153-177)
from sqlalchemy.dialects.postgresql import insert as pg_insert
predictions_table = get_table("predictions", engine)
chunk_size = 100
for i in range(0, len(records), chunk_size):
    chunk = records[i : i + chunk_size]
    stmt = pg_insert(predictions_table).values(chunk)
    update_columns = {
        col: stmt.excluded[col]
        for col in ["season", "week", "game_date", "home_team", "away_team",
                     "predicted_winner", "confidence", "confidence_tier",
                     "model_id", "actual_winner", "correct"]
    }
    upsert = stmt.on_conflict_do_update(index_elements=["game_id"], set_=update_columns)
    with engine.begin() as conn:
        conn.execute(upsert)
```

### Schedules Table Actual Outcomes
```python
# Source: sql/init.sql (schedules table has home_score, away_score, result)
# result column = home_score - away_score (this IS the actual spread)
# Can compute actual_spread directly from schedules:
# actual_spread = home_score - away_score
# actual_winner = home_team if actual_spread > 0 else away_team (ties: see convention)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pipeline has 4 steps | Pipeline has 5 steps (add spread) | Phase 10 | Spread predictions generated weekly |
| Only classifier seed exists | Spread seed script added | Phase 10 | Dashboard has historical spread data |
| Entrypoint seeds classifier only | Entrypoint seeds both models | Phase 10 | Spread model available in Docker |
| Worker has classifier env vars only | Worker has spread env vars too | Phase 10 | Worker can locate spread artifacts |

**Deprecated/outdated:**
- None. Phase 10 is additive -- no deprecations.

## Open Questions

1. **VPS deploy process**
   - What we know: Production runs at nostradamus.silverreyes.net. Docker Compose with nginx reverse proxy, postgres, api, and worker services.
   - What's unclear: Exact deploy steps (git pull + docker compose up? CI/CD pipeline? Manual SSH?).
   - Recommendation: Document deploy steps in the plan. Likely: SSH to VPS, git pull, docker compose build, docker compose up -d. Seed spread predictions should run after database is up but before the final deploy.

2. **Seed script execution environment**
   - What we know: `scripts/seed_predictions.py` runs with `python -m scripts.seed_predictions` and requires DATABASE_URL.
   - What's unclear: Should seed_spread.py run locally against the production DB, or inside a Docker container?
   - Recommendation: Run inside a Docker container using `docker compose exec api python -m scripts.seed_spread` (same environment, same DB access). Alternatively, run locally with production DATABASE_URL.

3. **Entrypoint guard for existing volumes**
   - What we know: Current guard checks `if [ ! -f "$MODEL_VOL/best_model.json" ]` -- if volume already has classifier model from v1.0, spread artifacts won't be seeded.
   - What's unclear: Whether production volume already has classifier artifacts.
   - Recommendation: Add a separate guard: `if [ ! -f "$MODEL_VOL/best_spread_model.json" ]` to handle the v1.0-to-v1.1 upgrade case.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (via pyproject.toml) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/test_pipeline.py -x` |
| Full suite command | `pytest tests/ features/tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-01 | Step 5 generates spread predictions in pipeline | unit | `pytest tests/test_pipeline.py::test_step5_generates_spread_predictions -x` | No -- Wave 0 |
| PIPE-01 | Step 5 failure is non-fatal | unit | `pytest tests/test_pipeline.py::test_step5_nonfatal_in_run_pipeline -x` | No -- Wave 0 |
| PIPE-01 | Step 5 skips in offseason | unit | `pytest tests/test_pipeline.py::test_step5_offseason_skips -x` | No -- Wave 0 |
| PIPE-01 | run_pipeline reads spread env vars | unit | `pytest tests/test_pipeline.py::test_run_pipeline_reads_spread_env_vars -x` | No -- Wave 0 |
| PIPE-02 | Seed script generates spread predictions for completed games | unit | `pytest tests/test_seed_spread.py::test_seed_spread_predictions -x` | No -- Wave 0 |
| PIPE-02 | Seed script backfills actual results | unit | `pytest tests/test_seed_spread.py::test_seed_spread_backfills_actuals -x` | No -- Wave 0 |
| PIPE-02 | Seed script is idempotent (upsert) | unit | `pytest tests/test_seed_spread.py::test_seed_spread_idempotent -x` | No -- Wave 0 |
| PIPE-03 | Docker compose has spread env vars for worker | manual-only | Inspect docker-compose.yml | N/A |
| PIPE-03 | Entrypoint seeds spread artifacts | manual-only | Inspect docker/entrypoint.sh | N/A |
| PIPE-03 | Production deploy successful | manual-only | Visit nostradamus.silverreyes.net | N/A |

### Sampling Rate
- **Per task commit:** `pytest tests/test_pipeline.py -x`
- **Per wave merge:** `pytest tests/ features/tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_pipeline.py` -- extend with step 5 tests (PIPE-01): non-fatal behavior, offseason skip, spread env var reading
- [ ] `tests/test_seed_spread.py` -- new file covering PIPE-02: seed generation, actuals backfill, idempotency
- [ ] No new framework install needed -- pytest already configured

## Sources

### Primary (HIGH confidence)
- `pipeline/refresh.py` -- Existing pipeline orchestration with steps 1-4, non-fatal pattern, env var reading
- `models/predict.py` -- Spread inference functions: `load_best_spread_model()`, `get_best_spread_experiment()`, `generate_spread_predictions()`
- `scripts/seed_predictions.py` -- Existing classifier seed script (pattern template)
- `docker-compose.yml` -- Current Docker service configuration
- `docker/entrypoint.sh` -- Current volume seeding logic
- `api/config.py` -- Settings class with `SPREAD_MODEL_PATH` and `SPREAD_EXPERIMENTS_PATH` already defined
- `sql/init.sql` -- `spread_predictions` table already exists (created in Phase 8)
- `tests/test_pipeline.py` -- Existing pipeline tests (extend with step 5 tests)

### Secondary (MEDIUM confidence)
- Phase 8 CONTEXT.md -- Spread inference architecture decisions and env var conventions

### Tertiary (LOW confidence)
- VPS deploy process -- inferred from Docker setup, not verified against actual server

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- all patterns are direct extensions of existing code, thoroughly verified against codebase
- Pitfalls: HIGH -- identified from direct code inspection and known v1.0-to-v1.1 upgrade concerns

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable -- no external dependency changes expected)
