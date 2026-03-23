---
phase: 07-spread-model-training
plan: 02
subsystem: training
tags: [xgboost, regression, spread, experiments, pseudo-huber, regularization]

# Dependency graph
requires:
  - phase: 07-spread-model-training/plan-01
    provides: Objective-flexible train_and_evaluate_spread(), spread_program.md, 14-test suite
provides:
  - Completed experiment sweep (Exps 2-4) with full JSONL logging
  - Production spread model (Exp 1 baseline, MAE 10.68)
  - Fully documented spread_program.md with results, dead ends, session log
affects: [phase-8]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pass dict copy ({**EXPERIMENT_PARAMS}) to train_and_evaluate_spread to prevent params.pop() mutation from losing logged params"

key-files:
  created: []
  modified:
    - models/train_spread.py
    - models/spread_experiments.jsonl
    - models/spread_program.md
    - models/artifacts/best_spread_model.json

key-decisions:
  - "Ship Exp 1 as production model -- no experiment beat baseline by >= 0.1 MAE threshold"
  - "Skip Exp 5 -- none of Exps 2-4 showed sufficient improvement to warrant combination"
  - "Fixed params.pop() mutation bug in run_spread_experiment() by passing dict copy"

patterns-established:
  - "NFL spread regression is near-optimal with default XGBoost hyperparams -- heavy-tailed target limits tuning gains"
  - "Pseudo-Huber loss provides negligible MAE improvement (0.002) on NFL point spreads"

requirements-completed: [TRAIN-01, TRAIN-02, TRAIN-03, TRAIN-04, TRAIN-05]

# Metrics
duration: 6min
completed: 2026-03-23
---

# Phase 7 Plan 2: Spread Experiment Sweep Summary

**Ran 3 targeted experiments (Pseudo-Huber loss, L2 regularization, lower learning rate) -- none beat Exp 1 by >= 0.1 MAE, shipping baseline as production model**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-23T15:26:40Z
- **Completed:** 2026-03-23T15:32:40Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Ran experiments 2-4 testing regression-specific optimizations (Pseudo-Huber loss, L2 regularization, lower learning rate)
- Confirmed Exp 1 baseline (MAE 10.68) is effectively optimal -- all alternatives produced marginal improvements (0.002 to 0.098)
- Updated spread_program.md with complete experiment results, dead ends documentation, and session log
- Fixed params.pop() mutation bug that caused objective parameter to be lost from JSONL log entries

## Experiment Results

| Exp | Configuration | MAE 2023 | Delta | Decision |
|-----|--------------|----------|-------|----------|
| 1 | Baseline (reg:squarederror, lr=0.1) | 10.683 | -- | KEEP |
| 2 | Pseudo-Huber loss (huber_slope=1.0) | 10.681 | 0.002 | REVERT |
| 3 | L2 reg_lambda=5.0 | 10.584 | 0.098 | REVERT |
| 4 | lr=0.05, n_est=500, patience=50 | 10.668 | 0.015 | REVERT |
| 5 | Combined best | -- | -- | SKIPPED |

## Task Commits

Each task was committed atomically:

1. **Task 1: Run experiments 2-4** - `c4ad814` (feat)
2. **Task 2: Update spread_program.md** - `d90bc7a` (docs)

## Files Created/Modified
- `models/train_spread.py` - Fixed params.pop() mutation by passing dict copy; config restored to Exp 1
- `models/spread_experiments.jsonl` - 3 new entries appended (Exps 2, 3, 4), total 4 entries
- `models/spread_program.md` - Complete results: experiment queue marked [x], dead ends documented, session log populated
- `models/artifacts/best_spread_model.json` - Exp 1 model (unchanged, still best)
- `models/artifacts/spread_model_exp001.json` - Exp 1 per-experiment snapshot (tracked)

## Decisions Made
- **Ship Exp 1 as production:** No experiment improved MAE by >= 0.1 (the keep threshold). Exp 3 came closest at delta 0.098, falling just 0.002 short. Per user decision in 07-CONTEXT.md: "if no experiment beats Exp 1, ship Exp 1."
- **Skip Exp 5:** The plan specified Exp 5 is conditional, only run if Exps 2-4 show improvement. None did, so Exp 5 was skipped.
- **Fix params mutation bug:** params.pop("objective") in train_and_evaluate_spread() mutated EXPERIMENT_PARAMS before logging, losing the objective key from JSONL entries. Fixed by passing `{**EXPERIMENT_PARAMS}` (a copy).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed params.pop() mutation losing objective from JSONL log**
- **Found during:** Task 1 (after running Exp 2)
- **Issue:** `train_and_evaluate_spread()` calls `params.pop("objective", ...)` which mutates the caller's dict. When `run_spread_experiment()` later logs `EXPERIMENT_PARAMS`, the `objective` key is already gone.
- **Fix:** Changed `EXPERIMENT_PARAMS` to `{**EXPERIMENT_PARAMS}` (shallow copy) in the call to `train_and_evaluate_spread()`
- **Files modified:** models/train_spread.py
- **Verification:** All 14 tests pass
- **Committed in:** c4ad814 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential for correct experiment logging. Exp 2's JSONL entry has huber_slope but missing objective key (pre-fix); future experiments will log correctly. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Production spread model (best_spread_model.json) is ready for Phase 8 API integration
- Model loads via `xgboost.XGBRegressor().load_model()` -- standard pattern for API lifespan handler
- Spread model MAE 10.68, beating both baselines (always +2.5: 11.02, always 0: 11.26)
- Phase 7 fully complete (2/2 plans done)
- All 14 spread training tests pass

## Self-Check: PASSED

All files exist, all commits verified.

---
*Phase: 07-spread-model-training*
*Completed: 2026-03-23*
