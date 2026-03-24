# Phase 8: Database and API Integration - Research

**Researched:** 2026-03-23
**Domain:** PostgreSQL schema, FastAPI endpoints, XGBoost spread inference pipeline
**Confidence:** HIGH

## Summary

Phase 8 extends the existing NFL Game Predictor API to serve spread predictions alongside classifier predictions. The codebase already has well-established patterns for every component needed: a `predictions` table (template for `spread_predictions`), endpoint routing in `api/routes/`, Pydantic schemas in `api/schemas.py`, lifespan model loading in `api/main.py`, and a complete prediction pipeline in `models/predict.py`. The spread model (XGBRegressor) is already trained and saved at `models/artifacts/best_spread_model.json`, and the experiment log at `models/spread_experiments.jsonl` contains all metadata needed.

This phase is primarily a "mirror and extend" effort -- the classifier patterns are proven and well-tested. The key differences are: (1) spread inference uses `model.predict()` instead of `model.predict_proba()`, (2) the best experiment is selected by lowest MAE instead of highest accuracy, (3) predicted_winner is derived from spread sign rather than from probability threshold, and (4) there is no confidence/confidence_tier concept for spread predictions.

**Primary recommendation:** Follow existing classifier patterns exactly. Add spread functions to `models/predict.py`, create a new `spread_predictions` table mirroring `predictions`, add a `spreads.py` route file, extend the lifespan handler and model info/reload endpoints, and add corresponding tests.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- New `spread_predictions` table with `game_id` as PRIMARY KEY (one prediction per game, upsert on re-prediction)
- Columns: game_id, season, week, game_date, home_team, away_team, predicted_spread (float), predicted_winner (derived at insert time), model_id, actual_spread, actual_winner, correct (boolean)
- predicted_winner derived from predicted_spread sign: >= 0 -> home team, < 0 -> away team (home-team convention for exact 0.0 ties)
- actual_spread + actual_winner stored as post-game actuals (not derived at query time)
- correct column populated when actual_winner is filled in, enabling easy accuracy queries
- Mirrors classifier predictions table pattern for consistency
- GET /api/predictions/spreads/week/{season}/{week} mirrors classifier endpoint response shape
- Per-game fields: game_id, season, week, game_date, home_team, away_team, predicted_spread, predicted_winner, actual_spread, actual_winner, correct
- GET /api/model/info keeps existing top-level classifier fields for backwards compatibility
- Adds a `spread_model` nested object with: mae, rmse, derived_win_accuracy, training_date, experiment_id
- If spread model not loaded: spread_model is null (not an error)
- If spread model file is missing, API still starts and serves classifier predictions normally
- Spread endpoints return 503 "Spread model not loaded" when spread model is absent
- /api/model/info returns spread_model: null when not loaded
- POST /api/model/reload extended to reload both classifier and spread model in one call
- Same token, single operation -- pipeline calls one endpoint to refresh everything
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

### Deferred Ideas (OUT OF SCOPE)
- Spread-specific /api/predictions/spreads/history endpoint -- may be needed in Phase 9 for dashboard history view
- Combined endpoint returning both classifier + spread predictions in one call -- evaluate if dashboard needs this in Phase 9

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | spread_predictions table stores per-game spread predictions with predicted_spread, predicted_winner, model_id, and post-game actuals | SQL DDL pattern from existing `predictions` table in `sql/init.sql`; upsert pattern from `generate_predictions()` in `models/predict.py` |
| API-02 | GET /api/predictions/spreads/week/{season}/{week} returns spread predictions per game for a given week | Endpoint pattern from `api/routes/predictions.py:get_week_predictions()`; Pydantic schema pattern from `api/schemas.py:PredictionResponse` |
| API-03 | GET /api/model/info includes spread model metadata (MAE, training date) alongside classifier info | Existing `ModelInfoResponse` schema and `model_info()` route in `api/routes/model.py`; spread experiment JSONL schema from `models/spread_experiments.jsonl` |
| API-04 | Spread model is loaded at API startup alongside the classifier via the lifespan handler | Lifespan pattern in `api/main.py:lifespan()`; graceful try/except pattern already used for classifier |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.115.0 | API framework | Already in use; lifespan, dependency injection, response models |
| SQLAlchemy | >=2.0 | Database ORM/reflection | Already in use; `get_table()` reflection, `pg_insert` upsert |
| psycopg | binary | PostgreSQL driver | Already in use; DATABASE_URL connection |
| XGBoost | >=3.2.0 | Spread model (XGBRegressor) | Already in use; `save_model()`/`load_model()` JSON format |
| Pydantic | (bundled with FastAPI) | Response schemas | Already in use via `BaseModel` subclasses |
| pandas | >=2.0 | SQL queries, DataFrame operations | Already in use for `pd.read_sql()` in routes |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | (installed) | Env var loading | Config settings for spread model paths |
| pytest | (dev dep) | Testing | API endpoint and predict.py tests |
| httpx | (dev dep) | FastAPI TestClient backend | Required by `fastapi.testclient.TestClient` |

No new dependencies are needed. All libraries are already installed.

**Installation:**
```bash
# No new packages needed -- all dependencies already in pyproject.toml
```

## Architecture Patterns

### Recommended Change Structure
```
sql/
  init.sql              # ADD spread_predictions table DDL

models/
  predict.py            # ADD load_best_spread_model(), get_best_spread_experiment(),
                        #     generate_spread_predictions()

api/
  config.py             # ADD SPREAD_MODEL_PATH, SPREAD_EXPERIMENTS_PATH settings
  deps.py               # UPDATE docstring (add spread_model, spread_model_info keys)
  schemas.py            # ADD SpreadPredictionResponse, SpreadWeekResponse,
                        #     SpreadModelInfo; UPDATE ModelInfoResponse
  main.py               # UPDATE lifespan() to load spread model; ADD import
  routes/
    spreads.py           # NEW: spread predictions endpoint
    model.py             # UPDATE model_info(), reload_model() for spread

tests/
  api/
    conftest.py          # UPDATE client fixture with spread mocks
    test_spreads.py      # NEW: spread endpoint tests
    test_model.py        # UPDATE: test spread_model in model_info response
  models/
    test_predict.py      # ADD: tests for spread predict functions
```

### Pattern 1: Spread Prediction Pipeline (mirrors classifier)
**What:** Three functions in `models/predict.py` that load, select, and generate spread predictions
**When to use:** At startup (load), for metadata (select), and during reload/pipeline (generate)
**Example:**
```python
# Source: models/predict.py (existing classifier pattern)
from xgboost import XGBRegressor

def load_best_spread_model(path: str = "models/artifacts/best_spread_model.json") -> XGBRegressor:
    """Load XGBoost spread model from artifact."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Spread model not found at '{path}'.")
    model = XGBRegressor()
    model.load_model(path)
    return model

def get_best_spread_experiment(jsonl_path: str = "models/spread_experiments.jsonl") -> dict | None:
    """Parse spread_experiments.jsonl for best kept experiment (lowest MAE)."""
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"Spread experiments not found at '{jsonl_path}'.")
    best = None
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("keep"):
                if best is None or entry["mae_2023"] < best["mae_2023"]:
                    best = entry
    if best is not None:
        best["model_path"] = best.get("model_path", "").replace("\\", "/")
    return best
```

### Pattern 2: Graceful Degradation in Lifespan
**What:** Try/except around spread model loading, API continues if spread model absent
**When to use:** Startup and reload
**Example:**
```python
# Source: api/main.py (existing classifier pattern extended)
@asynccontextmanager
async def lifespan(app: FastAPI):
    app_state["engine"] = get_engine()
    # Classifier (existing)
    try:
        app_state["model"] = load_best_model(settings.MODEL_PATH)
    except FileNotFoundError:
        app_state["model"] = None
    try:
        app_state["model_info"] = get_best_experiment(settings.EXPERIMENTS_PATH)
    except FileNotFoundError:
        app_state["model_info"] = None
    # Spread (new -- same pattern)
    try:
        app_state["spread_model"] = load_best_spread_model(settings.SPREAD_MODEL_PATH)
    except FileNotFoundError:
        app_state["spread_model"] = None
    try:
        app_state["spread_model_info"] = get_best_spread_experiment(settings.SPREAD_EXPERIMENTS_PATH)
    except FileNotFoundError:
        app_state["spread_model_info"] = None
    yield
    app_state.clear()
```

### Pattern 3: Upsert for Spread Predictions
**What:** PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` via SQLAlchemy
**When to use:** generate_spread_predictions() inserts or updates predictions per game
**Example:**
```python
# Source: models/predict.py:generate_predictions() (existing pattern)
from sqlalchemy.dialects.postgresql import insert as pg_insert

spread_table = get_table("spread_predictions", engine)
stmt = pg_insert(spread_table).values(records)
update_columns = {
    col: stmt.excluded[col]
    for col in ["season", "week", "game_date", "home_team", "away_team",
                "predicted_spread", "predicted_winner", "model_id",
                "actual_spread", "actual_winner", "correct"]
}
upsert = stmt.on_conflict_do_update(
    index_elements=["game_id"],
    set_=update_columns,
)
with engine.begin() as conn:
    conn.execute(upsert)
```

### Pattern 4: Spread Winner Derivation
**What:** Derive predicted_winner from predicted_spread sign at insert time
**When to use:** In generate_spread_predictions() when building records
**Example:**
```python
# Locked decision: >= 0 -> home team, < 0 -> away team
predicted_spread = float(model.predict(X)[i])
if predicted_spread >= 0:
    predicted_winner = home_team  # home-team convention for ties
else:
    predicted_winner = away_team
```

### Anti-Patterns to Avoid
- **Deriving predicted_winner at query time:** Locked decision stores it at insert time. Do NOT use CASE expressions in SQL queries.
- **Separate spread predict module:** Locked decision says all spread prediction code goes in `models/predict.py`, not a new file.
- **Breaking backwards compatibility:** Adding `spread_model` to ModelInfoResponse must be Optional so existing clients see null, not an error.
- **Blocking startup on missing spread model:** If spread model file is absent, API MUST still start. Use try/except, never let FileNotFoundError propagate.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Database upsert | Raw SQL INSERT/UPDATE with SELECT check | `sqlalchemy.dialects.postgresql.insert` + `on_conflict_do_update` | Race conditions, atomicity, existing pattern |
| Table reflection | Manual column definitions in Python | `get_table("spread_predictions", engine)` from `data/db.py` | Already abstracts reflection; DDL is source of truth |
| Model serialization | Custom pickle/joblib | `XGBRegressor.save_model()` / `load_model()` JSON format | Already used for classifier; portable, versionable |
| Response validation | Manual dict construction | Pydantic `BaseModel` subclasses | FastAPI auto-validates, auto-documents, type-safe |
| Config loading | Manual os.environ parsing | `api/config.py:Settings` class pattern | Centralized, testable, documented defaults |

**Key insight:** Every component in this phase has an existing classifier analog. The implementation should mirror those patterns exactly, only differing in the inference step (predict vs predict_proba) and selection metric (MAE vs accuracy).

## Common Pitfalls

### Pitfall 1: XGBRegressor vs XGBClassifier Type Mismatch
**What goes wrong:** Loading a regression model with `XGBClassifier()` or calling `predict_proba()` on an `XGBRegressor` causes errors.
**Why it happens:** The classifier pipeline uses `XGBClassifier().load_model()` and `model.predict_proba()`. Spread model must use `XGBRegressor` for both load and predict.
**How to avoid:** `load_best_spread_model()` must instantiate `XGBRegressor()` before calling `load_model()`. Inference must use `model.predict(X)` which returns raw spread values, not `predict_proba()`.
**Warning signs:** `ValueError: This method is not defined for Regressor object` at runtime.

### Pitfall 2: Spread Experiment JSONL Schema Differs from Classifier
**What goes wrong:** Attempting to parse spread experiments using classifier field names (e.g., `val_accuracy_2023`, `log_loss`, `brier_score`).
**Why it happens:** The spread JSONL uses different field names: `mae_2023`, `rmse_2023`, `derived_win_accuracy_2023`, and has a nested `baselines` dict. No `log_loss` or `brier_score` fields.
**How to avoid:** `get_best_spread_experiment()` must sort by `mae_2023` (ascending -- lowest is best) not `val_accuracy_2023`. The metadata extraction for model_info must map `mae_2023` -> `mae`, `rmse_2023` -> `rmse`, `derived_win_accuracy_2023` -> `derived_win_accuracy`.
**Warning signs:** KeyError on `val_accuracy_2023` when loading spread experiment info.

### Pitfall 3: Forgetting the model_path Backslash Normalization
**What goes wrong:** Windows paths in JSONL (e.g., `models/artifacts\\spread_model_exp001.json`) break on Linux/Docker.
**Why it happens:** The spread experiments JSONL was generated on Windows and contains backslashes.
**How to avoid:** Apply the same `.replace("\\", "/")` normalization already used in `get_best_experiment()`.
**Warning signs:** `FileNotFoundError` in production (Docker/Linux) but works locally on Windows.

### Pitfall 4: Test Client Fixture Must Mock Spread Dependencies
**What goes wrong:** Adding spread model loading to `lifespan()` without updating the test `client` fixture causes all API tests to fail.
**Why it happens:** The existing `conftest.py` patches specific lifespan imports. New spread imports must also be patched.
**How to avoid:** Update `tests/api/conftest.py` to patch `api.main.load_best_spread_model` and `api.main.get_best_spread_experiment` before adding the imports to `api/main.py`. Do fixture updates in the same task as lifespan changes.
**Warning signs:** `ModuleNotFoundError` or `FileNotFoundError` when running any existing API test.

### Pitfall 5: Nullable Fields in Spread Prediction Response
**What goes wrong:** API returns 422 Validation Error when spread predictions have NULL actual values.
**Why it happens:** Pydantic models default to required fields. `actual_spread`, `actual_winner`, and `correct` are NULL for unplayed games.
**How to avoid:** Define these as `Optional` in the Pydantic schema: `actual_spread: float | None = None`, `actual_winner: str | None = None`, `correct: bool | None = None`.
**Warning signs:** 422 responses on the spread endpoint for upcoming (unplayed) games.

### Pitfall 6: Spread Model Info Added as Required Field
**What goes wrong:** Existing /api/model/info endpoint returns 422 if `spread_model` is not in the response.
**Why it happens:** Adding `spread_model` as a required field in `ModelInfoResponse` breaks when no spread model is loaded.
**How to avoid:** Define as `spread_model: SpreadModelInfo | None = None`. The existing classifier fields remain top-level and unchanged.
**Warning signs:** 422/500 errors on `/api/model/info` after schema change, even though classifier model is loaded.

## Code Examples

Verified patterns from the existing codebase:

### SQL DDL for spread_predictions Table
```sql
-- Source: sql/init.sql (mirroring predictions table pattern)
CREATE TABLE IF NOT EXISTS spread_predictions (
    game_id VARCHAR(20) PRIMARY KEY,
    season SMALLINT NOT NULL,
    week SMALLINT NOT NULL,
    game_date DATE,
    home_team VARCHAR(3) NOT NULL,
    away_team VARCHAR(3) NOT NULL,
    predicted_spread REAL NOT NULL,
    predicted_winner VARCHAR(3) NOT NULL,
    model_id INTEGER,
    actual_spread REAL,
    actual_winner VARCHAR(3),
    correct BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_spread_predictions_season_week
    ON spread_predictions (season, week);
CREATE INDEX IF NOT EXISTS idx_spread_predictions_season
    ON spread_predictions (season);
```

### Pydantic Schemas
```python
# Source: api/schemas.py (mirroring PredictionResponse pattern)
class SpreadPredictionResponse(BaseModel):
    """Single game spread prediction."""
    game_id: str
    season: int
    week: int
    game_date: str | None = None
    home_team: str
    away_team: str
    predicted_spread: float
    predicted_winner: str
    actual_spread: float | None = None
    actual_winner: str | None = None
    correct: bool | None = None

class SpreadWeekResponse(BaseModel):
    """Response for GET /api/predictions/spreads/week/{season}/{week}."""
    season: int
    week: int
    status: str = "ok"
    predictions: list[SpreadPredictionResponse]

class SpreadModelInfo(BaseModel):
    """Spread model metadata nested in ModelInfoResponse."""
    mae: float
    rmse: float
    derived_win_accuracy: float
    training_date: str
    experiment_id: int

# Update existing ModelInfoResponse:
class ModelInfoResponse(BaseModel):
    experiment_id: int
    training_date: str
    val_accuracy_2023: float
    feature_count: int
    hypothesis: str
    baseline_always_home: float
    baseline_better_record: float
    spread_model: SpreadModelInfo | None = None  # NEW -- Optional
```

### Config Settings
```python
# Source: api/config.py (extending Settings pattern)
SPREAD_MODEL_PATH: str = os.environ.get(
    "SPREAD_MODEL_PATH", "models/artifacts/best_spread_model.json"
)
SPREAD_EXPERIMENTS_PATH: str = os.environ.get(
    "SPREAD_EXPERIMENTS_PATH", "models/spread_experiments.jsonl"
)
```

### Spread Route Endpoint
```python
# Source: api/routes/predictions.py (mirroring get_week_predictions pattern)
@router.get("/api/predictions/spreads/week/{season}/{week}",
            response_model=SpreadWeekResponse)
async def get_spread_predictions(
    season: int,
    week: int,
    state: dict = Depends(get_app_state),
):
    """Return spread predictions for a specific week."""
    if state.get("spread_model") is None:
        raise HTTPException(status_code=503, detail="Spread model not loaded")

    engine = state["engine"]
    query = """
        SELECT game_id, season, week, game_date, home_team, away_team,
               predicted_spread, predicted_winner,
               actual_spread, actual_winner, correct
        FROM spread_predictions
        WHERE season = %(season)s AND week = %(week)s
        ORDER BY game_date, game_id
    """
    df = pd.read_sql(query, engine, params={"season": season, "week": week})
    # ... build response (same pattern as classifier)
```

### generate_spread_predictions Key Differences from Classifier
```python
# Source: models/predict.py:generate_predictions() adapted for spread
# Difference 1: Inference is model.predict() not model.predict_proba()
spreads = model.predict(X)  # Returns raw spread values (float array)

# Difference 2: Winner derived from spread sign, not probability threshold
for i, (_, game) in enumerate(unplayed.iterrows()):
    predicted_spread = float(spreads[i])
    if predicted_spread >= 0:
        predicted_winner = game["home_team"]
    else:
        predicted_winner = game["away_team"]

# Difference 3: No confidence/confidence_tier concept
record = {
    "game_id": str(game["game_id"]),
    "season": int(game["season"]),
    "week": int(game["week"]),
    "game_date": game_date,
    "home_team": str(game["home_team"]),
    "away_team": str(game["away_team"]),
    "predicted_spread": predicted_spread,
    "predicted_winner": str(predicted_winner),
    "model_id": model_id,
    "actual_spread": None,
    "actual_winner": None,
    "correct": None,
}

# Difference 4: Upsert to "spread_predictions" table, not "predictions"
spread_table = get_table("spread_predictions", engine)
```

### Model Info Extension
```python
# Source: api/routes/model.py:model_info() extended
spread_info = state.get("spread_model_info")
spread_model_data = None
if spread_info is not None:
    spread_model_data = SpreadModelInfo(
        mae=spread_info["mae_2023"],
        rmse=spread_info["rmse_2023"],
        derived_win_accuracy=spread_info["derived_win_accuracy_2023"],
        training_date=spread_info["timestamp"],
        experiment_id=spread_info["experiment_id"],
    )

return ModelInfoResponse(
    # ... existing classifier fields ...
    spread_model=spread_model_data,
)
```

### Reload Extension
```python
# Source: api/routes/model.py:reload_model() extended
# After reloading classifier model (existing code)...

# Reload spread model
try:
    new_spread_model = load_best_spread_model(settings.SPREAD_MODEL_PATH)
    new_spread_info = get_best_spread_experiment(settings.SPREAD_EXPERIMENTS_PATH)
    state["spread_model"] = new_spread_model
    state["spread_model_info"] = new_spread_info
except FileNotFoundError:
    state["spread_model"] = None
    state["spread_model_info"] = None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Classifier only | Classifier + spread regression | Phase 7 (2026-03-23) | Two models serving complementary predictions |
| Single model in app_state | Multiple models in app_state dict | Phase 8 (this phase) | app_state keys expand; graceful degradation per model |
| Single predictions table | Separate predictions + spread_predictions tables | Phase 8 (this phase) | Clean separation; no schema migration needed |

**No deprecated patterns to worry about.** All current patterns (FastAPI lifespan, SQLAlchemy 2.0+ style, Pydantic v2) are modern and stable.

## Open Questions

1. **Should there be a /api/predictions/spreads/current convenience endpoint?**
   - What we know: The classifier has `/api/predictions/current` that auto-resolves to the current unplayed week. The same `detect_current_week()` function is reusable.
   - What's unclear: Whether dashboard Phase 9 will need this or always use explicit season/week.
   - Recommendation: Add it -- it's 10 lines of code, reuses `detect_current_week()`, and follows the classifier pattern. If Phase 9 does not need it, it does no harm.

2. **Should spread route go in existing predictions.py or new spreads.py?**
   - What we know: The existing `predictions.py` has 3 classifier endpoints (week, current, history). CONTEXT.md notes "Route files split by concern -- spread predictions can go in existing predictions.py or new spread.py".
   - Recommendation: Use a new `api/routes/spreads.py` file. This keeps the spread endpoint isolated, makes testing cleaner (separate mock setup), and avoids making `predictions.py` overly large. Register it via `app.include_router(spreads.router)` in `main.py`.

3. **ReloadResponse schema update for spread model info**
   - What we know: The current `ReloadResponse` returns `experiment_id`, `val_accuracy_2023`, `predictions_generated` for the classifier.
   - Recommendation: Add optional spread fields: `spread_experiment_id: int | None = None`, `spread_mae: float | None = None`, `spread_predictions_generated: int = 0`. This keeps backwards compatibility while confirming spread was reloaded.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (via pyproject.toml) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/api/ -x -q` |
| Full suite command | `pytest tests/ features/tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | spread_predictions table DDL + upsert works | unit (mock DB) | `pytest tests/models/test_predict.py::test_get_best_spread_experiment -x` | No -- Wave 0 |
| API-01 | generate_spread_predictions builds correct records | unit | `pytest tests/models/test_predict.py::test_generate_spread_predictions -x` | No -- Wave 0 |
| API-01 | predicted_winner derived correctly from spread sign | unit | `pytest tests/models/test_predict.py::test_spread_winner_derivation -x` | No -- Wave 0 |
| API-02 | GET /api/predictions/spreads/week/{season}/{week} returns 200 | unit (TestClient) | `pytest tests/api/test_spreads.py::test_get_spread_week -x` | No -- Wave 0 |
| API-02 | Spread endpoint returns 503 when model not loaded | unit (TestClient) | `pytest tests/api/test_spreads.py::test_spread_503_no_model -x` | No -- Wave 0 |
| API-03 | GET /api/model/info includes spread_model when loaded | unit (TestClient) | `pytest tests/api/test_model.py::test_model_info_with_spread -x` | No -- Wave 0 |
| API-03 | GET /api/model/info returns spread_model=null when not loaded | unit (TestClient) | `pytest tests/api/test_model.py::test_model_info_no_spread -x` | No -- Wave 0 |
| API-04 | Lifespan loads spread model into app_state | unit (TestClient) | `pytest tests/api/test_spreads.py::test_spread_model_loaded -x` | No -- Wave 0 |
| API-04 | API starts successfully when spread model file missing | unit (TestClient) | `pytest tests/api/test_spreads.py::test_startup_no_spread_model -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/api/ tests/models/test_predict.py -x -q`
- **Per wave merge:** `pytest tests/ features/tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/api/test_spreads.py` -- covers API-02, API-04 (spread endpoint + startup behavior)
- [ ] `tests/api/conftest.py` update -- add spread model mocks to client fixtures
- [ ] `tests/api/test_model.py` update -- add spread_model field tests for API-03
- [ ] `tests/models/test_predict.py` update -- add spread predict function tests for API-01

## Sources

### Primary (HIGH confidence)
- `api/main.py` -- Lifespan handler pattern (lines 15-31)
- `api/routes/predictions.py` -- Endpoint pattern for week predictions (lines 18-83)
- `api/routes/model.py` -- Model info and reload patterns (lines 18-103)
- `api/schemas.py` -- All Pydantic response models (lines 1-99)
- `api/config.py` -- Settings class pattern (lines 10-29)
- `api/deps.py` -- app_state dependency injection (lines 1-16)
- `sql/init.sql` -- Existing predictions table DDL (lines 130-146)
- `models/predict.py` -- Full classifier prediction pipeline (lines 1-322)
- `models/train_spread.py` -- Spread model structure and JSONL schema (lines 1-536)
- `models/spread_experiments.jsonl` -- Actual experiment entries with field names
- `tests/api/conftest.py` -- TestClient fixture with mock patterns (lines 1-203)

### Secondary (MEDIUM confidence)
- Research into `XGBRegressor.load_model()` behavior -- confirmed same API as `XGBClassifier.load_model()` from XGBoost documentation pattern

### Tertiary (LOW confidence)
- None -- all findings are based on direct codebase inspection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies; all libraries already in pyproject.toml
- Architecture: HIGH -- every component mirrors an existing classifier analog in the codebase
- Pitfalls: HIGH -- identified from actual code patterns and field name differences in JSONL schemas

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable -- internal codebase patterns, no external API changes expected)
