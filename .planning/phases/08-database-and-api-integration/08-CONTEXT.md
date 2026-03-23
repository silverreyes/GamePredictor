# Phase 8: Database and API Integration - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Spread predictions are stored in the database and served via API endpoints alongside the existing classifier predictions. Includes a new spread_predictions table, dedicated spread API endpoint, spread metadata in /api/model/info, and spread model loading at startup. Dashboard integration is Phase 9; pipeline/seeding is Phase 10.

</domain>

<decisions>
## Implementation Decisions

### Spread table schema
- New `spread_predictions` table with `game_id` as PRIMARY KEY (one prediction per game, upsert on re-prediction)
- Columns: game_id, season, week, game_date, home_team, away_team, predicted_spread (float), predicted_winner (derived at insert time), model_id, actual_spread, actual_winner, correct (boolean)
- predicted_winner derived from predicted_spread sign: >= 0 -> home team, < 0 -> away team (home-team convention for exact 0.0 ties)
- actual_spread + actual_winner stored as post-game actuals (not derived at query time)
- correct column populated when actual_winner is filled in, enabling easy accuracy queries
- Mirrors classifier predictions table pattern for consistency

### API response design
- GET /api/predictions/spreads/week/{season}/{week} mirrors classifier endpoint response shape
- Per-game fields: game_id, season, week, game_date, home_team, away_team, predicted_spread, predicted_winner, actual_spread, actual_winner, correct
- Consistent shape with classifier predictions makes dashboard consumption straightforward

### Model info structure
- GET /api/model/info keeps existing top-level classifier fields for backwards compatibility
- Adds a `spread_model` nested object with: mae, rmse, derived_win_accuracy, training_date, experiment_id
- If spread model not loaded: spread_model is null (not an error)

### Graceful degradation
- If spread model file is missing, API still starts and serves classifier predictions normally
- Spread endpoints return 503 "Spread model not loaded" when spread model is absent
- /api/model/info returns spread_model: null when not loaded

### Model reload
- POST /api/model/reload extended to reload both classifier and spread model in one call
- Same token, single operation — pipeline calls one endpoint to refresh everything

### Spread inference pipeline
- All spread prediction code added to existing `models/predict.py` (not a separate module)
- New functions: load_best_spread_model(), get_best_spread_experiment(), generate_spread_predictions()
- Reuses classifier's feature pipeline: same build_game_features() call, same _get_team_rolling_features()
- Only inference step differs: model.predict() (regression) instead of model.predict_proba() (classifier)
- Tie convention: predicted_spread >= 0 -> home wins, < 0 -> away wins
- get_best_spread_experiment() selects by lowest MAE among keep=true entries (MAE is primary metric from Phase 7)

### Claude's Discretion
- Exact SQL DDL for spread_predictions table (indexes, data types)
- Pydantic schema naming and structure details
- Config settings for spread model path and experiments path env vars
- Whether to add a /api/predictions/spreads/current convenience endpoint
- Test strategy and coverage

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — API-01 through API-04 define all Phase 8 requirements
- `.planning/ROADMAP.md` §Phase 8 — Success criteria (4 items)

### Existing API patterns (follow these)
- `api/main.py` — Lifespan handler pattern for model loading, app_state dict, router registration
- `api/routes/predictions.py` — Classifier predictions endpoint pattern (query + response construction)
- `api/routes/model.py` — Model info and reload endpoint patterns
- `api/schemas.py` — Pydantic response model patterns
- `api/config.py` — Settings class with env var loading pattern
- `api/deps.py` — app_state dependency injection pattern

### Database schema
- `sql/init.sql` — Existing table definitions (predictions table is the template for spread_predictions)

### Prediction pipeline
- `models/predict.py` — load_best_model(), get_best_experiment(), generate_predictions(), _get_team_rolling_features() — spread functions go alongside these
- `models/train_spread.py` — Spread training script (defines model output format, JSONL logging structure)
- `models/spread_experiments.jsonl` — Spread experiment log (schema for get_best_spread_experiment to parse)
- `models/artifacts/best_spread_model.json` — Spread model artifact path

### Phase 7 context
- `.planning/phases/07-spread-model-training/07-CONTEXT.md` — Spread model decisions (MAE primary metric, Exp 1 as production model)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `models/predict.py:load_best_model()` — Pattern for loading XGBoost JSON model (spread version loads XGBRegressor instead of XGBClassifier)
- `models/predict.py:get_best_experiment()` — Pattern for parsing JSONL for best kept experiment (spread version sorts by lowest MAE instead of highest accuracy)
- `models/predict.py:generate_predictions()` — Full prediction pipeline pattern: build features, get rolling stats, run inference, upsert (spread version replaces proba -> predict, confidence -> spread)
- `models/predict.py:_get_team_rolling_features()` — Shared directly by spread inference (no changes needed)
- `api/schemas.py:PredictionResponse` — Template for SpreadPredictionResponse schema
- `api/schemas.py:ModelInfoResponse` — Needs spread_model field added

### Established Patterns
- PostgreSQL upsert via sqlalchemy pg_insert + on_conflict_do_update — used in generate_predictions()
- app_state dict for runtime model state — add spread_model and spread_model_info keys
- Environment-based config via Settings class — add SPREAD_MODEL_PATH and SPREAD_EXPERIMENTS_PATH
- Route files split by concern — spread predictions can go in existing predictions.py or new spread.py

### Integration Points
- `api/main.py:lifespan()` — Add spread model loading alongside classifier (try/except for graceful degradation)
- `api/deps.py:app_state` — Add spread_model and spread_model_info keys
- `api/routes/model.py:model_info()` — Extend response with spread_model object
- `api/routes/model.py:reload_model()` — Extend to reload spread model + regenerate spread predictions
- `sql/init.sql` — Add spread_predictions table DDL
- `data/db.py:get_table()` — Will work for new table via SQLAlchemy reflection

</code_context>

<specifics>
## Specific Ideas

- Home-team convention for tie edge case (predicted_spread = 0.0) must be consistent between insert-time derivation and any downstream logic
- User explicitly noted: storing predicted_winner avoids CASE expressions in every SQL query and maintains consistency with classifier table
- Backwards compatibility matters: existing dashboard reads /api/model/info top-level fields, adding spread_model as a nested object preserves this

</specifics>

<deferred>
## Deferred Ideas

- Spread-specific /api/predictions/spreads/history endpoint — may be needed in Phase 9 for dashboard history view
- Combined endpoint returning both classifier + spread predictions in one call — evaluate if dashboard needs this in Phase 9

</deferred>

---

*Phase: 08-database-and-api-integration*
*Context gathered: 2026-03-23*
