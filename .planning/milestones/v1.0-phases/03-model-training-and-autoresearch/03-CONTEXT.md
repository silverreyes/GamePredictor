# Phase 3: Model Training and Autoresearch - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Train an XGBoost win/loss classifier via a governed experiment loop that achieves >60% accuracy on the 2023 validation season, beating both trivial baselines (always-home ~57%, better-record ~60%). Full experiment logging to experiments.jsonl and MLflow. Temporal split is fixed: train 2005-2022, val 2023, holdout 2024.

</domain>

<decisions>
## Implementation Decisions

### Experiment queue design (program.md)
- program.md uses an experiment queue with prioritized ordering: **vary the signal first, then tune the noise**
- Queue order: (1) baseline XGBoost defaults, (2) feature ablation studies (drop turnovers, drop EPA, drop rest days/div flag), (3) hyperparameter tuning (learning_rate, max_depth), (4) regularization (reg_lambda) last
- program.md must include termination conditions: stop after 20 experiments total OR 3 consecutive <0.3% improvements OR 2021/2022 accuracy degrades while 2023 improves
- program.md must include a "Dead Ends (Do Not Retry)" section to prevent re-trying failed approaches
- "Current Best" section tracks 2021/2022/2023 accuracy side-by-side so overfitting is visible at a glance

### Keep/revert mechanism
- Git-based: agent edits models/train.py (uncommitted), runs training, then either commits on keep or `git checkout -- models/train.py` on revert
- **Commit only on keep** — git log becomes a clean record of changes that stuck
- experiments.jsonl is append-only and captures everything (kept and reverted) — two complementary audit trails
- **Compound keep rule**: keep if (a) accuracy improves by >=0.5%, OR (b) accuracy improves by any amount AND log_loss also improves. Otherwise revert. This prevents random-walking through noise on the 272-game 2023 validation set.

### Experiment logging schema (experiments.jsonl)
- Rich entries: experiment ID, timestamp, params dict, features list used, val accuracies (2023, 2022, 2021), baseline comparisons (always-home, better-record), log_loss, brier_score, TreeSHAP top-5 features, keep/revert status, hypothesis text, prev_best_acc
- log_loss and brier_score are mandatory — accuracy alone is insufficient for detecting calibration issues ("56% with calibrated probabilities beats 58% with garbage confidence scores")

### Session limit
- Hard stop at 5 experiments per session (ceiling, not target)
- Termination conditions override: if 3 consecutive experiments show <0.3% improvement within a session, stop early rather than burning remaining slots on a plateau
- At session end, agent updates program.md: mark completed experiments, update Current Best, update Dead Ends, suggest next 5 experiments
- The "suggest next 5" handoff is what makes session boundaries cheap — next session starts warm with no ramp-up cost
- The 5-experiment limit bounds decision compounding risk: each keep/revert changes the baseline for the next experiment, and bad keeps compound

### Baseline computation
- Baselines computed **once upfront** before the experiment loop starts, stored in program.md as fixed reference numbers
- Separate module: `models/baselines.py` — never modified during experiments (only train.py is modified)
- **Better-record baseline**: predict winner as the team with more wins so far that season. Ties broken by prior season record. Home-team fallback only when no prior season data exists (e.g., first season in dataset)
- **Tied games excluded** from baseline and model accuracy calculation — both measured on the same ~271 game set (apples-to-apples)
- Both baseline accuracies logged in every experiments.jsonl entry for immediate comparison

### Claude's Discretion
- MLflow tracking configuration (local file-based vs server)
- MLflow experiment naming and artifact storage
- Model serialization format (pickle, joblib, etc.) and where artifacts live on disk
- TreeSHAP visualization approach
- Exact XGBoost default parameters for experiment #1
- How NaN week-1 rows are handled (drop vs impute)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Experiment governance
- `CLAUDE.md` — Critical rules: only modify models/train.py during experiments, experiments.jsonl is append-only, program.md lives at models/program.md, 5 experiment max per session, temporal split is hardcoded
- `.planning/REQUIREMENTS.md` — MODL-01 through MODL-07: full requirements for model training, logging, baselines, autoresearch loop, and TreeSHAP

### Feature pipeline (read-only context)
- `features/definitions.py` — ROLLING_FEATURES, SITUATIONAL_FEATURES, TARGET, FORBIDDEN_FEATURES lists
- `features/build.py` — `build_game_features()` entry point returns complete feature matrix

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `features/build.py:build_game_features()` — Returns full feature DataFrame with home_rolling_*, away_rolling_*, situational columns, and home_win target
- `features/definitions.py` — Canonical lists of feature names, target variable, and forbidden features
- `data/db.py:get_engine()` — SQLAlchemy engine for loading feature data from PostgreSQL

### Established Patterns
- Feature columns follow `home_rolling_{stat}` / `away_rolling_{stat}` naming convention
- Target variable is `home_win` (1=home win, 0=away win, None=tie)
- Per-season rolling reset via groupby(['team', 'season']) with expanding window
- Week 1 of each season has NaN rolling features (correct behavior from shift(1))

### Integration Points
- `models/` directory does not exist yet — needs to be created with train.py, baselines.py, program.md
- XGBoost, MLflow, SHAP are not in project dependencies yet — need to be added to pyproject.toml
- Feature matrix can be loaded from PostgreSQL game_features table or built directly via build_game_features()

</code_context>

<specifics>
## Specific Ideas

- Queue ordering principle: "vary the signal first, then tune the noise" — feature ablation before hyperparameter tuning, because optimal hyperparams shift when features change
- The session boundary's value is in the "suggest next 5" handoff, not the count itself — next session starts warm
- Two complementary audit trails: git log for what stuck, experiments.jsonl for everything tried
- Compound keep rule uses the fact that log_loss captures probability calibration quality that binary accuracy misses

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-model-training-and-autoresearch*
*Context gathered: 2026-03-16*
