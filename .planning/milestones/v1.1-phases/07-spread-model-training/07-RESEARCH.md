# Phase 7: Spread Model Training - Research

**Researched:** 2026-03-23
**Domain:** XGBoost regression optimization, experiment tracking, NFL spread prediction
**Confidence:** HIGH

## Summary

Phase 7 formalizes an already-working spread regression prototype (`models/train_spread.py`) into a production-grade training pipeline with a targeted experiment sweep and formal experiment tracking. The prototype already satisfies all 5 TRAIN requirements -- it trains an XGBRegressor, evaluates on multiple seasons with baselines, logs to JSONL, and saves artifacts. The core work is running 3-5 regression-specific experiments (objective functions, regularization tuning) and creating a `spread_program.md` experiment program document.

The prototype mirrors the classifier pipeline (`models/train.py`) structurally. The current Exp 1 baseline uses `reg:squarederror` with classifier Exp 5 hyperparams (lr=0.1, max_depth=6, n_estimators=300, early_stopping=20), achieving MAE 10.68 on 2023 validation. The model stopped at iteration 9 via early stopping, suggesting very fast convergence. Naive baselines are MAE 11.02 (always +2.5) and MAE 11.26 (always 0) -- the model already beats both.

**Primary recommendation:** Run a targeted 3-5 experiment sweep focused on `reg:pseudohubererror` (outlier-robust loss), `reg_alpha`/`reg_lambda` L1/L2 regularization, and early stopping patience tuning. Create `spread_program.md` following the classifier `program.md` format. If no experiment beats Exp 1 by >= 0.1 MAE, ship Exp 1 as production.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Targeted sweep of 3-5 experiments focused on regression-specific parameters
- Not a full autoresearch loop -- classifier already proved all 17 features and Exp 5 hyperparams are near-optimal
- Focus areas: objective function variants (e.g., pseudohuberloss for outlier robustness), reg_alpha/reg_lambda tuning for regression, early stopping patience
- Fixed experiment budget -- run the planned sweep and stop, no dynamic stopping conditions
- If no experiment beats Exp 1 baseline (MAE 10.68), ship Exp 1 as the production model
- MAE is the primary metric -- this is a regression model, MAE directly measures spread prediction quality
- Derived win accuracy and RMSE are reported but secondary
- SHAP top-5 features continue to be logged per experiment
- Keep if MAE improves by >= 0.1 points (current threshold, ~1% relative improvement)
- MAE-only gating -- no secondary metric guards on the keep decision
- All metrics still logged for analysis (derived win accuracy, RMSE, overfitting monitoring on 2021/2022)
- Create a separate `models/spread_program.md` for spread experiment program
- Tracks experiment queue, hypotheses, dead ends, and session logs
- Separate from classifier's `models/program.md` -- different metrics, baselines, and dead ends
- `spread_experiments.jsonl` continues as the machine-readable append-only log

### Claude's Discretion
- Specific experiments in the 3-5 experiment queue (which regression params to try)
- spread_program.md structure and format
- Code cleanup/refactoring of train_spread.py if needed for production readiness
- Whether to add spread-specific tests

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TRAIN-01 | Training script produces XGBRegressor model predicting home point differential using same 17 features and temporal split as classifier | Already met by prototype. train_spread.py uses all 17 features, temporal split 2005-2022/2023/2024. Experiment loop modifies EXPERIMENT_PARAMS module-level vars, not the split logic. |
| TRAIN-02 | Training evaluates MAE, RMSE, and derived win accuracy on 2023 validation, plus MAE/RMSE on 2021 and 2022 for overfitting monitoring | Already met by prototype. train_and_evaluate_spread() returns all 9 metrics (3 per season). Printed and logged. |
| TRAIN-03 | Training computes and logs naive baselines (always +2.5 and always 0) for comparison | Already met by prototype. compute_spread_baselines() computes both. Logged in JSONL under "baselines" key. |
| TRAIN-04 | Experiments are logged to spread_experiments.jsonl (append-only) with full metadata | Already met by prototype. log_spread_experiment() appends complete entry with params, metrics, baselines, SHAP, keep decision. |
| TRAIN-05 | Best spread model is saved as best_spread_model.json alongside classifier artifacts | Already met by prototype. save_best_spread_model() writes to models/artifacts/best_spread_model.json. |

</phase_requirements>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| xgboost | 3.2.0 | XGBRegressor for spread prediction | Same as classifier, native JSON save/load, TreeSHAP support |
| shap | 0.51.0 | TreeSHAP feature importance | Top-5 feature logging per experiment |
| scikit-learn | 1.8.0 | mean_absolute_error, root_mean_squared_error | Standard metrics, already imported |
| pandas | 2.3.3 | Data manipulation, temporal splits | Feature matrix handling |
| numpy | 2.4.3 | Array operations, baseline computation | Prediction arrays, SHAP aggregation |

### Supporting (Already Installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | N/A | JSONL logging | Append-only experiment log |
| datetime (stdlib) | N/A | UTC timestamps | Experiment metadata |

### No New Dependencies Required

All libraries needed are already installed and imported in `train_spread.py`. No `pip install` needed for this phase.

## Architecture Patterns

### Existing Project Structure (No Changes Needed)
```
models/
  train_spread.py        # Spread training pipeline (prototype, modify per experiment)
  train.py               # Classifier pipeline (DO NOT MODIFY)
  program.md             # Classifier experiment program (template reference)
  spread_program.md      # NEW: Spread experiment program
  spread_experiments.jsonl # Append-only spread experiment log (1 entry exists)
  artifacts/
    best_spread_model.json     # Current best spread model
    spread_model_exp001.json   # Per-experiment model snapshots
    best_model.json            # Classifier best (DO NOT TOUCH)
    model_exp001.json          # Classifier snapshots (DO NOT TOUCH)
```

### Pattern 1: Module-Level Experiment Configuration
**What:** Each experiment modifies module-level variables (`EXPERIMENT_ID`, `EXPERIMENT_PARAMS`, `EXPERIMENT_HYPOTHESIS`, `DROP_FEATURES`) rather than CLI arguments.
**When to use:** Every experiment run.
**Example:**
```python
# Experiment 2: Pseudo-Huber loss for outlier robustness
EXPERIMENT_ID = 2
EXPERIMENT_PARAMS = {
    **DEFAULT_SPREAD_PARAMS,
    "objective": "reg:pseudohubererror",  # Override default squarederror
}
EXPERIMENT_HYPOTHESIS = (
    "Pseudo-Huber loss reduces impact of blowout outliers "
    "(NFL margins have heavy tails, SD ~14.7 vs mean ~2.2)"
)
DROP_FEATURES: list[str] = []
```
**Source:** Established in `models/train.py` classifier pipeline, mirrored in `train_spread.py`.

### Pattern 2: Objective Function Override in train_and_evaluate_spread
**What:** The `train_and_evaluate_spread()` function currently hardcodes `objective="reg:squarederror"`. To test different objectives, the objective must come from the `params` dict.
**When to use:** When running experiments with `reg:pseudohubererror` or other objective functions.
**Critical change needed:**
```python
# BEFORE (current prototype, line 195-199):
model = XGBRegressor(
    objective="reg:squarederror",
    eval_metric="mae",
    **params,
)

# AFTER (allow objective override from params):
objective = params.pop("objective", "reg:squarederror")
model = XGBRegressor(
    objective=objective,
    eval_metric="mae",
    **params,
)
```
**Why:** Without this change, passing `objective` in `EXPERIMENT_PARAMS` will conflict with the hardcoded kwarg.

### Pattern 3: Keep/Revert Decision (Simpler Than Classifier)
**What:** For spread regression, the keep decision uses MAE-only gating: keep if `prev_best_mae - results["mae_2023"] >= 0.1`.
**When to use:** After every experiment except Exp 1.
**Example:** Already implemented in `run_spread_experiment()` lines 474-482.

### Anti-Patterns to Avoid
- **Modifying train.py or features/build.py:** CLAUDE.md forbids this. Only `train_spread.py` changes during experiments.
- **Shuffling temporal splits:** CLAUDE.md: train 2005-2022, val 2023, holdout 2024 -- never shuffle.
- **Deleting JSONL entries:** experiments.jsonl and spread_experiments.jsonl are append-only.
- **Running more than 5 experiments per session:** CLAUDE.md 5-experiment cap.
- **Using result, home_score, or away_score as features:** CLAUDE.md forbidden features.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Huber loss function | Custom loss with gradient/hessian | `objective="reg:pseudohubererror"` + `huber_slope` param | XGBoost has built-in Pseudo-Huber since v1.2, twice-differentiable, handles gradient/hessian automatically |
| Early stopping | Manual epoch loop with patience tracking | `early_stopping_rounds` param in XGBRegressor | Native XGBoost feature, already used in prototype |
| Feature importance | Manual feature weight extraction | `shap.TreeExplainer` with TreeSHAP | Already implemented, exact SHAP values not approximations |
| Model serialization | Pickle or joblib | `model.save_model()` / `model.load_model()` with JSON format | XGBoost native format, version-compatible, human-readable |

## Common Pitfalls

### Pitfall 1: Hardcoded Objective Prevents Experiment Flexibility
**What goes wrong:** `train_and_evaluate_spread()` hardcodes `objective="reg:squarederror"`. Passing `"objective"` in params dict will cause a TypeError (duplicate keyword argument).
**Why it happens:** Prototype was built for squared error only.
**How to avoid:** Extract objective from params before passing to XGBRegressor constructor, with `"reg:squarederror"` as default.
**Warning signs:** TypeError on experiment run.

### Pitfall 2: Pseudo-Huber min_child_weight Sensitivity
**What goes wrong:** Historical XGBoost issue where `reg:pseudohubererror` with default `min_child_weight=1` could produce poor results (predicting constants).
**Why it happens:** Pseudo-Huber gradient behaves differently than squared error near the origin.
**How to avoid:** On XGBoost 3.2.0, `base_score` is automatically estimated (fixed in v2.0+). The old issue is resolved, but worth monitoring -- if Pseudo-Huber experiment shows constant predictions, try `min_child_weight=0` or explicit `base_score=median(y_train)`.
**Warning signs:** All predictions identical, MAE doesn't decrease across iterations.

### Pitfall 3: Early Stopping Converges at Iteration 9
**What goes wrong:** Current model stops at iteration 9 out of 300 (with patience 20). This means the model is barely training -- learning rate may be too high for this target distribution.
**Why it happens:** NFL point differentials are noisy (SD ~14.7), the signal-to-noise ratio is low, and the model quickly finds the mean/median prediction is hard to beat.
**How to avoid:** This is actually expected behavior for this problem. Don't over-tune -- early stopping at a low iteration count means the dataset doesn't support more complex models. Reducing learning rate with more estimators may help explore more of the loss surface.
**Warning signs:** If best_iteration increases dramatically (e.g., 200+) without MAE improvement, the model is overfitting to validation noise.

### Pitfall 4: NFL Point Spread Distribution Has Heavy Tails
**What goes wrong:** Squared error penalizes blowout games disproportionately. A 45-point blowout has 2025x the squared error of a 1-point game.
**Why it happens:** NFL margins have mean ~2.2 but SD ~14.7. Blowouts (15+ point margins) occur in ~2 out of every 7 games.
**How to avoid:** This is precisely why `reg:pseudohubererror` is worth testing -- it uses absolute error for large deviations and squared error for small ones. The `huber_slope` parameter (default 1.0) controls the transition point.
**Warning signs:** If MAE improves but RMSE stays the same or worsens, the model is better at typical games but worse at blowouts (which may be acceptable).

### Pitfall 5: Spread JSONL Schema Differs from Classifier
**What goes wrong:** Accidentally importing classifier `log_experiment()` instead of spread-specific `log_spread_experiment()`.
**Why it happens:** Similar function names in parallel modules.
**How to avoid:** Spread logging uses different keys: `mae_2023` instead of `val_accuracy_2023`, `model_type: "spread_regression"`, `baselines` dict instead of separate baseline fields.
**Warning signs:** KeyError when reading JSONL entries.

## Code Examples

### Example 1: Running a Spread Experiment (Established Pattern)
```python
# In models/train_spread.py, modify module-level vars:
EXPERIMENT_ID = 2
EXPERIMENT_PARAMS = {
    **DEFAULT_SPREAD_PARAMS,
    # Override specific params for this experiment
}
EXPERIMENT_HYPOTHESIS = "Description of what this experiment tests"
DROP_FEATURES: list[str] = []

# Then run:
# python -m models.train_spread
```
Source: Existing pattern in `models/train.py` and `models/train_spread.py`.

### Example 2: Pseudo-Huber Loss Configuration
```python
# XGBoost reg:pseudohubererror with huber_slope tuning
EXPERIMENT_PARAMS = {
    **DEFAULT_SPREAD_PARAMS,
    "objective": "reg:pseudohubererror",
    "huber_slope": 1.0,  # Default; controls transition from L2 to L1
    # huber_slope < 1.0 = more L1-like (more outlier robust)
    # huber_slope > 1.0 = more L2-like (closer to squared error)
}
```
Source: [XGBoost Parameters Documentation](https://xgboost.readthedocs.io/en/stable/parameter.html)

### Example 3: L1/L2 Regularization Tuning
```python
# reg_alpha (L1) promotes sparsity, reg_lambda (L2) penalizes large weights
EXPERIMENT_PARAMS = {
    **DEFAULT_SPREAD_PARAMS,
    "reg_alpha": 1.0,   # L1 regularization (default 0, try 0.1, 1.0, 10.0)
    "reg_lambda": 5.0,  # L2 regularization (default 1, try 0.1, 1.0, 5.0, 10.0)
}
```
Source: [XGBoost Parameters Documentation](https://xgboost.readthedocs.io/en/stable/parameter.html)

### Example 4: Spread Program Document Structure (Based on Classifier program.md)
```markdown
# Spread Experiment Program

## Baselines (Fixed Reference)
- Always +2.5 MAE (2023): 11.02
- Always 0 MAE (2023): 11.26
- Classifier-derived win accuracy (2023): 62.89%

## Current Best
| Metric | Value |
|--------|-------|
| MAE 2023 | 10.68 |
| RMSE 2023 | 13.87 |
| Derived Win Acc 2023 | 60.16% |
| MAE 2022 | 8.71 |
| MAE 2021 | 10.61 |

Best experiment: **Exp 1** (baseline, reg:squarederror, lr=0.1)

## Experiment Queue
- [ ] Exp 2: Pseudo-Huber loss (outlier robustness)
- [ ] Exp 3: L1/L2 regularization tuning
- [ ] Exp 4: Early stopping patience + lower learning rate
- [ ] Exp 5: (Optional) Best of above combined

## Dead Ends (Do Not Retry)
(Updated after experiments)

## Session Log
(Updated after experiments)
```
Source: Pattern from `models/program.md`.

## Recommended Experiment Queue

Based on the existing baseline and classifier experience, here are the recommended 3-5 experiments:

### Exp 2: Pseudo-Huber Loss for Outlier Robustness
**Hypothesis:** NFL point margins have heavy tails (SD ~14.7, mean ~2.2). Pseudo-Huber loss reduces the outsized influence of blowout games, potentially improving MAE on typical-margin games.
**Params:** `objective="reg:pseudohubererror"`, `huber_slope=1.0`, all other params from Exp 1.
**Rationale:** Theoretically motivated -- squared error penalizes 45-point blowouts 2025x more than 1-point games. Pseudo-Huber transitions from L2 to L1 for large deviations.

### Exp 3: L2 Regularization (reg_lambda)
**Hypothesis:** Increasing L2 regularization constrains leaf weights, reducing overfitting on the noisy spread target. Current reg_lambda=1 (default).
**Params:** `reg_lambda=5.0` (or sweep [1, 3, 5, 10]), all other params from Exp 1.
**Rationale:** Classifier experience showed Exp 5 hyperparams were near-optimal, but the spread target is noisier than binary win/loss. Higher regularization may help.

### Exp 4: Lower Learning Rate + More Trees + Longer Patience
**Hypothesis:** The model currently stops at iteration 9. A lower learning rate with more estimators and longer patience may allow more gradual optimization of the loss surface.
**Params:** `learning_rate=0.05`, `n_estimators=500`, `early_stopping_rounds=50`.
**Rationale:** Classifier Exp 8 (lr=0.01) nearly beat Exp 5 at 63.28% accuracy. The spread model may benefit similarly from slower learning.

### Exp 5 (Optional): Combined Best
**Hypothesis:** Combine the best-performing changes from Exps 2-4.
**Params:** Best objective + best regularization + best learning rate schedule.
**Rationale:** Only run if any of Exps 2-4 show improvement or promising direction.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded base_score=0.5 | Auto-estimated base_score | XGBoost 2.0 | Pseudo-Huber loss now works correctly out-of-the-box |
| reg:squarederror only | Multiple regression objectives | XGBoost 1.2+ | pseudohubererror, absoluteerror, quantileerror available |
| Pickle model serialization | Native JSON save_model() | XGBoost 1.0+ | Version-compatible, human-readable artifacts |

**Current in project:**
- XGBoost 3.2.0 (latest stable) -- all features available
- Auto base_score estimation -- no manual workarounds needed

## Open Questions

1. **Will Pseudo-Huber loss improve MAE or just change the error distribution?**
   - What we know: It should reduce influence of blowouts, potentially improving median prediction quality
   - What's unclear: Whether MAE (mean of absolute errors) improves when the model de-emphasizes extreme games, since MAE already uses absolute differences
   - Recommendation: Run the experiment; if MAE doesn't improve but error distribution narrows (fewer large errors), note it in the program as an interesting finding

2. **Is the model's early convergence (iteration 9) a problem or a feature?**
   - What we know: Low signal-to-noise ratio in NFL spreads (SD ~14.7) means models quickly learn the mean and can't improve much
   - What's unclear: Whether a slower learning rate would find a better optimum or just take longer to reach the same one
   - Recommendation: Exp 4 tests this directly. If best_iteration stays ~9 even with lr=0.05, the data simply doesn't support deeper models

3. **Should `huber_slope` be tuned or left at default?**
   - What we know: Default is 1.0. Lower values = more outlier robust, higher = closer to squared error
   - What's unclear: Optimal value for NFL point spread distribution
   - Recommendation: Start with default 1.0. If Pseudo-Huber shows promise, optionally try 0.5 and 2.0 as sub-experiments within the 5-experiment budget

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (no version pin, installed as dev dependency) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/models/ -x -q` |
| Full suite command | `python -m pytest tests/ features/tests/ -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRAIN-01 | XGBRegressor trains with 17 features + temporal split | unit | `python -m pytest tests/models/test_train_spread.py::TestSpreadSplit -x` | No -- Wave 0 |
| TRAIN-02 | MAE, RMSE, derived win acc on 2023 + MAE/RMSE on 2021/2022 | unit | `python -m pytest tests/models/test_train_spread.py::TestSpreadEval -x` | No -- Wave 0 |
| TRAIN-03 | Naive baselines computed and logged | unit | `python -m pytest tests/models/test_train_spread.py::TestSpreadBaselines -x` | No -- Wave 0 |
| TRAIN-04 | JSONL logging with full metadata | unit | `python -m pytest tests/models/test_train_spread.py::TestSpreadLogging -x` | No -- Wave 0 |
| TRAIN-05 | Model saved as best_spread_model.json | unit | `python -m pytest tests/models/test_train_spread.py::TestSpreadModelSave -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/models/test_train_spread.py -x -q`
- **Per wave merge:** `python -m pytest tests/ features/tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/models/test_train_spread.py` -- covers TRAIN-01 through TRAIN-05 (spread split, eval, baselines, logging, model save)
  - Pattern: Mirror `tests/models/test_train.py` and `tests/models/test_logging.py` structure
  - Key differences from classifier tests: regression metrics (MAE/RMSE not accuracy/logloss), spread_target not home_win, baselines are constants not computed from data
- [ ] Shared conftest fixtures in `tests/models/conftest.py` may need spread-specific synthetic data with `spread_target` column (continuous values, not binary)

**Note on existing conftest.py:** The current `tests/models/conftest.py` has `ROLLING_COLS` and `sample_feature_df` with binary `home_win` target. Spread tests need a similar fixture with continuous `spread_target` values. The fixture can be added to the same conftest or a new spread-specific one.

## Sources

### Primary (HIGH confidence)
- [XGBoost 3.2.0 Parameters Documentation](https://xgboost.readthedocs.io/en/stable/parameter.html) -- regression objectives, huber_slope, reg_alpha/reg_lambda
- `models/train_spread.py` (local) -- complete working prototype, 535 lines
- `models/train.py` (local) -- classifier pipeline template, 451 lines
- `models/spread_experiments.jsonl` (local) -- Exp 1 baseline results
- `models/program.md` (local) -- classifier experiment program template

### Secondary (MEDIUM confidence)
- [XGBoost Issue #10988](https://github.com/dmlc/xgboost/issues/10988) -- pseudohubererror base_score fix, confirmed resolved in XGBoost 2.0+
- [XGBoost Issue #5852](https://github.com/dmlc/xgboost/issues/5852) -- pseudohubererror availability, confirmed in XGBoost 1.2+
- [XGBoosting.com: Configure reg:pseudohubererror](https://xgboosting.com/configure-xgboost-regpseudohubererror-objective/) -- usage patterns
- [nfeloapp.com: NFL Margin Probabilities](https://www.nfeloapp.com/analysis/margin-probabilities-from-nfl-spreads/) -- NFL spread distribution statistics (mean ~2.2, SD ~14.7)

### Tertiary (LOW confidence)
- NFL blowout frequency claim ("2 out of 7 games are 15+ point blowouts") -- from web search, not independently verified against project data

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and verified, no new dependencies
- Architecture: HIGH -- prototype is complete and working, patterns directly from codebase
- Pitfalls: HIGH -- objective function hardcoding verified in source code, XGBoost version compatibility confirmed
- Experiment queue: MEDIUM -- experiments are theoretically motivated but outcomes are inherently uncertain

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable -- no fast-moving dependencies)
