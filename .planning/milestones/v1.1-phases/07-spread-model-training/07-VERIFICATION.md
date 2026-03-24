---
phase: 07-spread-model-training
verified: 2026-03-23T16:10:00Z
status: passed
score: 5/5 success criteria verified
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  gaps_closed:
    - "Each training run appends a complete entry to spread_experiments.jsonl with model params, metrics, and timestamp (Exp 2 now includes objective: reg:pseudohubererror)"
  gaps_remaining: []
  regressions: []
---

# Phase 7: Spread Model Training Verification Report

**Phase Goal:** A validated, production-ready spread model with reproducible training, proper evaluation against baselines, and experiment logging
**Verified:** 2026-03-23T16:10:00Z
**Status:** passed
**Re-verification:** Yes -- after gap closure (07-03-PLAN.md)

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Running train_spread.py produces best_spread_model.json that loads successfully with XGBoost | VERIFIED | `models/artifacts/best_spread_model.json` exists (193,954 bytes); `params.pop` at line 195 and `{**EXPERIMENT_PARAMS}` dict copy at line 455 confirmed in-place |
| 2 | Training output reports MAE, RMSE, derived win accuracy on 2023 validation, plus MAE/RMSE on 2021 and 2022 | VERIFIED | `train_and_evaluate_spread()` logs all 9 metric keys; all 4 JSONL entries contain mae_2023, rmse_2023, derived_win_accuracy_2023, mae_2022, rmse_2022, derived_win_accuracy_2022, mae_2021, rmse_2021, derived_win_accuracy_2021; 14 tests pass covering these metrics |
| 3 | Training output reports naive baselines and spread model beats both on MAE | VERIFIED | `compute_spread_baselines()` confirmed; Exp 1 MAE 10.683 beats always+2.5 (11.023) and always-0 (11.258); JSONL entries all include `baselines` key |
| 4 | Each training run appends a complete entry to spread_experiments.jsonl with model params, metrics, and timestamp | VERIFIED | 4 entries present; all have 20 top-level keys; Exp 2 params dict now contains `"objective": "reg:pseudohubererror"` and `"huber_slope": 1.0` (gap closure confirmed); wiring is correct -- `log_spread_experiment` receives original `EXPERIMENT_PARAMS` (not the mutated copy), so all keys survive |
| 5 | Model artifact is saved alongside classifier artifacts in models/artifacts/ | VERIFIED | `models/artifacts/best_spread_model.json` (193,954 bytes) alongside `best_model.json`, `spread_model_exp001.json` |

**Score:** 5/5 success criteria verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `models/train_spread.py` | Objective-flexible training function | VERIFIED | 536 lines; `params.pop("objective", "reg:squarederror")` at line 195; `{**EXPERIMENT_PARAMS}` dict copy at line 455; all 6 public functions present |
| `models/spread_program.md` | Spread experiment program document | VERIFIED | All sections populated: Baselines, Current Best, Keep/Revert Threshold, Experiment Queue (5 [x] items), Dead Ends (3 entries), Session Log (Session 1 with correction note for gap closure) |
| `tests/models/test_train_spread.py` | Spread training pipeline tests (min 80 lines) | VERIFIED | 477 lines; 5 test classes; 14 tests; all 14 pass in 2.42s |
| `models/spread_experiments.jsonl` | Complete experiment log (min 4 entries) | VERIFIED | 4 lines; all 4 entries have 20 keys; Exp 2 params now contains `objective: reg:pseudohubererror`; Exp 3 has `reg_lambda: 5.0`; Exp 4 has `learning_rate: 0.05` |
| `models/artifacts/best_spread_model.json` | Production spread model artifact | VERIFIED | 193,954 bytes; Exp 1 model (MAE 10.683) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/models/test_train_spread.py` | `models/train_spread.py` | import | WIRED | `from models.train_spread import` confirmed in file |
| `models/train_spread.py` | `models/spread_experiments.jsonl` | JSONL append | WIRED | `spread_experiments.jsonl` at lines 463 and 502; file opened with `"a"` mode in `log_spread_experiment()` |
| `models/train_spread.py` | `models/artifacts/best_spread_model.json` | save_best_spread_model | WIRED | `best_spread_model.json` in `save_best_spread_model()` called from `run_spread_experiment()` |
| `run_spread_experiment()` | `log_spread_experiment()` | function call | WIRED | Called at line 491-502 with `params=EXPERIMENT_PARAMS` (original dict, not mutated copy); `params.pop()` was called on `{**EXPERIMENT_PARAMS}` copy at line 455 so original is intact |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| TRAIN-01 | 07-01, 07-02 | XGBRegressor training with same 17 features and temporal split as classifier | SATISFIED | `load_and_split_spread()` enforces 2005-2022 train / 2023 val split; `feature_cols` excludes FORBIDDEN_FEATURES; `TestSpreadSplit` tests all boundaries |
| TRAIN-02 | 07-01, 07-02 | Evaluates MAE, RMSE, derived win accuracy on 2023 val plus MAE/RMSE on 2021 and 2022 | SATISFIED | `train_and_evaluate_spread()` returns 9 metrics across 3 seasons; all present in every JSONL entry; `TestSpreadEval` verifies all keys |
| TRAIN-03 | 07-01, 07-02 | Computes and logs naive baselines (always +2.5 and always 0) for comparison | SATISFIED | `compute_spread_baselines()` computes both; logged in each JSONL entry under `baselines` key; Exp 1 MAE 10.683 beats both baselines |
| TRAIN-04 | 07-01, 07-02, 07-03 | Experiments logged to spread_experiments.jsonl (append-only) with full metadata | SATISFIED | 4 entries logged; all 20 required keys present in all entries; Exp 2 params now includes `objective: reg:pseudohubererror` (patched by 07-03); `log_spread_experiment` receives original params dict (not mutated copy) |
| TRAIN-05 | 07-01, 07-02 | Best spread model saved as best_spread_model.json alongside classifier artifacts | SATISFIED | `models/artifacts/best_spread_model.json` exists alongside `best_model.json`; `save_best_spread_model()` called from `run_spread_experiment()` when keep=True |

**Orphaned requirements:** None -- all 5 phase-7 requirements claimed in plans match REQUIREMENTS.md traceability table.

### Anti-Patterns Found

None. The Exp 2 params logging gap (the sole anti-pattern from the initial verification) has been resolved. No placeholder implementations, empty handlers, stub returns, or TODO comments remain in the production files.

### Human Verification Required

None -- all success criteria are verifiable programmatically for this training/ML phase.

### Gap Closure Summary

**One gap from initial verification -- fully closed:**

The previous verification found that Exp 2's JSONL entry was missing `"objective": "reg:pseudohubererror"` in its params dict due to a `params.pop()` mutation bug that stripped the key before logging.

**Resolution applied (07-03-PLAN.md):**
- `models/spread_experiments.jsonl` Exp 2 entry was patched in-place to add `"objective": "reg:pseudohubererror"` as the first key in params (before n_estimators), preserving all other fields unchanged
- `models/spread_program.md` Session 1 log was updated with a correction note documenting the root cause and the fix
- All 4 entries remain valid JSON with 20 top-level keys each
- The code fix (`{**EXPERIMENT_PARAMS}` dict copy at line 455) was already in place from 07-02; the patch brought the historical record into compliance

**Re-verification outcome:** All 5 success criteria pass. No regressions in previously-passing items. Phase 7 goal is achieved.

---

## Detailed Evidence

### JSONL State After Gap Closure (all 4 entries)

| Exp | keep | mae_2023 | objective in params |
|-----|------|----------|-------------------|
| 1 | true | 10.6826 | (none -- reg:squarederror default) |
| 2 | false | 10.6811 | reg:pseudohubererror (patched) |
| 3 | false | 10.5836 | (none -- reg:squarederror default) |
| 4 | false | 10.6677 | (none -- reg:squarederror default) |

### Baseline Beat Verification

| | MAE 2023 |
|--|---------|
| Spread Model (Exp 1) | 10.683 |
| Always +2.5 baseline | 11.023 |
| Always 0 baseline | 11.258 |

Model beats both baselines: confirmed.

### Wiring Correctness: params.pop() vs log_spread_experiment()

The key architectural detail: `run_spread_experiment()` calls `train_and_evaluate_spread({**EXPERIMENT_PARAMS}, ...)` at line 455 -- passing a shallow copy. Inside `train_and_evaluate_spread`, `params.pop("objective", "reg:squarederror")` at line 195 removes `objective` from the COPY only. When `log_spread_experiment(params=EXPERIMENT_PARAMS, ...)` is called at line 491, it receives the original `EXPERIMENT_PARAMS` dict, which still contains all keys including `objective`. This is why Exps 3 and 4 were logged correctly without patching.

### Test Suite

- 14 tests across 5 classes: TestSpreadSplit (4), TestSpreadEval (4), TestSpreadBaselines (2), TestSpreadLogging (2), TestSpreadModelSave (2)
- All 14 pass in 2.42s (re-verified post gap closure)

---

_Verified: 2026-03-23T16:10:00Z_
_Verifier: Claude (gsd-verifier)_
_Re-verification after: 07-03-PLAN.md gap closure_
