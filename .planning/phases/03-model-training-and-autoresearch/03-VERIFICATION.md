---
phase: 03-model-training-and-autoresearch
verified: 2026-03-17T19:44:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 3: Model Training and Autoresearch Verification Report

**Phase Goal:** An XGBoost win/loss classifier achieves above 60% accuracy on the 2023 validation season, beating both trivial baselines, via a governed experiment loop with full logging
**Verified:** 2026-03-17T19:44:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (derived from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Model trained on 2005-2022, validated on 2023, 2024 held out | VERIFIED | `load_and_split` uses `between(2005, 2022)` and `== 2023`; 2024 only appears in "NEVER touched" docstring comment |
| 2 | Every experiment logs to both experiments.jsonl and MLflow with all required fields | VERIFIED | All 5 experiments have 16/16 required keys; `mlflow.start_run` called in `log_experiment`; JSONL open with mode "a" |
| 3 | Autoresearch loop reads program.md, modifies only train.py, keeps if improved else reverts | VERIFIED | 2 kept / 3 reverted experiments in jsonl; program.md exists with 5 checked-off experiments; git log shows keep commits `91a9d54`, `407e81c` |
| 4 | Best model beats always-home (~57%) and better-record (~60%) on 2023 validation | VERIFIED | Best model (Exp 5): 62.89% vs always-home 55.51% and better-record 58.20% |
| 5 | At least 5 logged experiments with keep/revert decisions | VERIFIED | Exactly 5 experiments in experiments.jsonl (2 kept, 3 reverted) |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `models/__init__.py` | Package init for models module | VERIFIED | Exists (empty package init) |
| `models/baselines.py` | Baseline computation functions | VERIFIED | 190 lines; exports `always_home_baseline`, `better_record_baseline`, `compute_baselines`, `_build_prior_season_records`; imports `TARGET` from `features.definitions` |
| `tests/models/test_baselines.py` | Unit tests for baseline computation | VERIFIED | 273 lines (min 40 required); 10 test functions including prior-season tiebreaker and home-fallback |
| `tests/models/conftest.py` | Synthetic feature DataFrames for model tests | VERIFIED | 131 lines (min 30 required); contains `sample_feature_df`, `home_rolling_win`, `away_rolling_win` |
| `models/train.py` | Training pipeline with temporal split, dual logging, SHAP | VERIFIED | 484 lines (min 120 required); exports all 7 required functions |
| `tests/models/test_train.py` | Unit tests for temporal split, multi-season eval, SHAP logging | VERIFIED | 293 lines (min 80 required); 11 test functions |
| `tests/models/test_logging.py` | Unit tests for dual logging | VERIFIED | 244 lines (min 40 required); 4 test functions |
| `models/program.md` | Experiment queue, current best, dead ends | VERIFIED | 84 lines (min 50 required); contains all required sections with actual baseline values |
| `models/experiments.jsonl` | Append-only experiment log with 5+ entries | VERIFIED | 5 JSON lines; all entries have full 16-field schema |
| `models/artifacts/best_model.json` | XGBoost model beating both baselines | VERIFIED | 186 KB XGBoost native JSON format (Exp 5 configuration) |
| `models/artifacts/model_exp001.json` | Exp 1 model artifact | VERIFIED | 481 KB |
| `models/artifacts/model_exp005.json` | Exp 5 model artifact | VERIFIED | 186 KB |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `models/baselines.py` | `features/definitions.py` | `from features.definitions import TARGET` | WIRED | Line 1 of baselines.py: `from features.definitions import TARGET` |
| `tests/models/test_baselines.py` | `models/baselines.py` | `from models.baselines import ...` | WIRED | Test file imports baseline functions directly |
| `models/train.py` | `features/build.py` | `from features.build import build_game_features` | WIRED | `run_experiment()` deferred import of `build_game_features` at line 371 |
| `models/train.py` | `features/definitions.py` | `from features.definitions import TARGET, FORBIDDEN_FEATURES` | WIRED | Line 27: `from features.definitions import FORBIDDEN_FEATURES, TARGET` |
| `models/train.py` | `models/baselines.py` | `from models.baselines import compute_baselines` | WIRED | `run_experiment()` deferred import at line 372 |
| `models/train.py` | `models/experiments.jsonl` | `open(..., "a")` append JSON entry | WIRED | `log_experiment` opens jsonl with mode "a" (lines 233-234) |
| `models/train.py` | `models/program.md` | Agent reads program.md to select next experiment | WORKFLOW ONLY | No code import — this is a conceptual/workflow link. The agent reads program.md externally before modifying train.py. Cannot be verified programmatically; verified by git commit history showing experiments follow program.md queue order (Exp 1 baseline -> Exp 2-4 ablations -> Exp 5 hyperparams) |
| `models/train.py` | `models/artifacts/` | `save_model` writes XGBoost JSON | WIRED | `save_model` function uses `os.makedirs` + `model.save_model(path)` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| MODL-01 | 03-02-PLAN.md | XGBoost classifier with temporal split: train 2005-2022, val 2023, holdout 2024 | SATISFIED | `load_and_split` enforces hardcoded boundaries; all 5 experiments used this split |
| MODL-02 | 03-02-PLAN.md | Every training run logs params, 2023 validation accuracy, and model artifact path to experiments.jsonl and MLflow | SATISFIED | All 5 experiments have full 16-field JSONL schema and MLflow runs via `log_experiment` |
| MODL-03 | 03-01-PLAN.md | Every training run logs trivial baseline accuracies alongside model accuracy from experiment #1 onward | SATISFIED | `baseline_always_home` and `baseline_better_record` present in all 5 experiments; computed via `compute_baselines` |
| MODL-04 | 03-02-PLAN.md | Every training run logs val accuracy on 2021 and 2022 alongside 2023 for overfitting detection | SATISFIED | `val_accuracy_2022` and `val_accuracy_2021` present in all 5 JSONL entries |
| MODL-05 | 03-03-PLAN.md | Autoresearch loop: reads program.md, modifies only train.py, keeps if 2023 accuracy improves, reverts otherwise | SATISFIED | git log shows 2 keep commits; reverted exps logged with `keep: false`; program.md queue followed in order |
| MODL-06 | 03-03-PLAN.md | Model beats both trivial baselines on 2023 validation before production-ready | SATISFIED | Exp 5: 62.89% > always-home 55.51% and better-record 58.20% |
| MODL-07 | 03-02-PLAN.md | TreeSHAP feature importance computed post-training and logged to experiments.jsonl, not at inference time | SATISFIED | `shap.TreeExplainer` called in `train_and_evaluate`; top-5 SHAP in all 5 JSONL entries with `feature`/`importance` keys |

All 7 required MODL requirements are SATISFIED. No orphaned requirements found.

---

### Anti-Patterns Found

No anti-patterns detected. Scanned `models/train.py`, `models/baselines.py`, and `models/program.md` for:
- TODO/FIXME/PLACEHOLDER comments: none found
- Empty implementations (return null, return {}, return []): none found
- Stub handlers: none found

One UserWarning noted: `use_label_encoder` parameter in XGBClassifier is deprecated in XGBoost 3.x. This is a cosmetic warning only — it does not affect model training, accuracy, or functionality. Not a blocker.

---

### Human Verification Required

#### 1. Program.md as Autoresearch Driver

**Test:** Review `models/program.md` experiment queue ordering vs `models/experiments.jsonl` experiment IDs 1-5 to confirm experiments were executed in queue order.
**Expected:** Exp 1 = Baseline, Exp 2-4 = Feature Ablations (matching Phase 2 in program.md), Exp 5 = Hyperparameter Tuning (matching Phase 3 Exp 5 in program.md)
**Why human:** The `train.py -> program.md` key link is a workflow relationship — the agent reads program.md externally, not via code import. Queue adherence can only be confirmed by reading both files together.

#### 2. MLflow Experiment Dashboard

**Test:** Run `mlflow ui` from the project root and navigate to http://127.0.0.1:5000
**Expected:** 5 experiment runs visible under "nfl-game-predictor" experiment with params, metrics (val_accuracy_2023, log_loss, etc.) and keep/revert tags
**Why human:** MLflow UI rendering and completeness require browser inspection; automated grep cannot verify UI correctness.

---

## Test Suite Summary

| Suite | Result |
|-------|--------|
| `pytest tests/models/` | 25 passed, 6 warnings |
| `pytest tests/ features/tests/` (full suite) | 76 passed, 3 skipped, 6 warnings |

Full test suite is green with no failures.

---

## Phase Goal Assessment

**Goal:** "An XGBoost win/loss classifier achieves above 60% accuracy on the 2023 validation season, beating both trivial baselines, via a governed experiment loop with full logging"

All components of this goal are verified:
- Above 60% accuracy: Exp 5 achieves 62.89% on 2023 validation (goal: >60%)
- Beats always-home baseline: 62.89% vs 55.51% (+7.38pp)
- Beats better-record baseline: 62.89% vs 58.20% (+4.69pp)
- Governed experiment loop: 5 experiments with keep/revert decisions, git commit audit trail
- Full logging: 16-field JSONL schema + MLflow dual logging on every experiment

---

_Verified: 2026-03-17T19:44:00Z_
_Verifier: Claude (gsd-verifier)_
