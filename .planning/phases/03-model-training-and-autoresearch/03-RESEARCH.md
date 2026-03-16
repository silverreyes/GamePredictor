# Phase 3: Model Training and Autoresearch - Research

**Researched:** 2026-03-16
**Domain:** XGBoost binary classification, MLflow experiment tracking, SHAP explainability, autoresearch loop governance
**Confidence:** HIGH

## Summary

Phase 3 builds the model training infrastructure and autoresearch experiment loop for an NFL game win/loss classifier. The core stack is XGBoost (binary classification), MLflow (experiment tracking), and SHAP (TreeExplainer for feature importance). The training data is 4,639 games (2005-2022), validated on 272 games (2023 season), with 272 games held out (2024). This is a relatively small tabular dataset where XGBoost is the established best-in-class approach.

The primary challenge is not the model itself (XGBoost binary classification is straightforward) but the governance infrastructure: the autoresearch loop, the compound keep/revert mechanism, dual logging (experiments.jsonl + MLflow), baseline computation, and the multi-season overfitting detection. The feature pipeline from Phase 2 produces 17 features (7 home rolling, 7 away rolling, 3 situational) with the target `home_win`. Week 1 rows have NaN rolling features and must be handled (drop is the simplest correct approach).

**Primary recommendation:** Structure this phase as three plans: (1) baselines + training infrastructure + MLflow setup, (2) experiment logging + TreeSHAP + program.md template, (3) autoresearch loop execution with 5+ experiments. Use XGBoost's native `save_model()` (JSON format) for model persistence, local file-based MLflow tracking, and manual MLflow logging (not autolog) for full control over what gets recorded.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Experiment queue design (program.md):** program.md uses an experiment queue with prioritized ordering: "vary the signal first, then tune the noise." Queue order: (1) baseline XGBoost defaults, (2) feature ablation studies (drop turnovers, drop EPA, drop rest days/div flag), (3) hyperparameter tuning (learning_rate, max_depth), (4) regularization (reg_lambda) last. program.md must include termination conditions: stop after 20 experiments total OR 3 consecutive <0.3% improvements OR 2021/2022 accuracy degrades while 2023 improves. program.md must include a "Dead Ends (Do Not Retry)" section to prevent re-trying failed approaches. "Current Best" section tracks 2021/2022/2023 accuracy side-by-side so overfitting is visible at a glance.
- **Keep/revert mechanism:** Git-based: agent edits models/train.py (uncommitted), runs training, then either commits on keep or `git checkout -- models/train.py` on revert. Commit only on keep -- git log becomes a clean record of changes that stuck. experiments.jsonl is append-only and captures everything (kept and reverted) -- two complementary audit trails. Compound keep rule: keep if (a) accuracy improves by >=0.5%, OR (b) accuracy improves by any amount AND log_loss also improves. Otherwise revert. This prevents random-walking through noise on the 272-game 2023 validation set.
- **Experiment logging schema (experiments.jsonl):** Rich entries: experiment ID, timestamp, params dict, features list used, val accuracies (2023, 2022, 2021), baseline comparisons (always-home, better-record), log_loss, brier_score, TreeSHAP top-5 features, keep/revert status, hypothesis text, prev_best_acc
- **Session limit:** Hard stop at 5 experiments per session (ceiling, not target). Termination conditions override: if 3 consecutive experiments show <0.3% improvement within a session, stop early rather than burning remaining slots on a plateau. At session end, agent updates program.md: mark completed experiments, update Current Best, update Dead Ends, suggest next 5 experiments.
- **Baseline computation:** Baselines computed once upfront before the experiment loop starts, stored in program.md as fixed reference numbers. Separate module: `models/baselines.py` -- never modified during experiments (only train.py is modified). Better-record baseline: predict winner as the team with more wins so far that season. Ties broken by prior season record. Home-team fallback only when no prior season data exists. Tied games excluded from baseline and model accuracy calculation -- both measured on the same ~271 game set (apples-to-apples).

### Claude's Discretion
- MLflow tracking configuration (local file-based vs server)
- MLflow experiment naming and artifact storage
- Model serialization format (pickle, joblib, etc.) and where artifacts live on disk
- TreeSHAP visualization approach
- Exact XGBoost default parameters for experiment #1
- How NaN week-1 rows are handled (drop vs impute)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MODL-01 | System trains an XGBoost win/loss classifier with temporal split: train 2005-2022, validate 2023, holdout 2024 | XGBoost XGBClassifier with `objective='binary:logistic'`; temporal split via pandas season filtering; 4,639 train / 272 val / 272 holdout games |
| MODL-02 | Every training run logs params, 2023 validation accuracy, and model artifact path to experiments.jsonl and MLflow | Manual MLflow logging via `mlflow.log_params()`, `mlflow.log_metrics()`, `mlflow.log_artifact()`; JSONL append via standard `json` module |
| MODL-03 | Every training run logs trivial baseline accuracies (always-home, better-record) on the 2023 validation season alongside model accuracy | `models/baselines.py` computes both baselines once; values stored as constants and logged in every experiment entry |
| MODL-04 | Every training run logs validation accuracy on 2021 and 2022 seasons for overfitting detection | Evaluate trained model on 2021 (272 games) and 2022 (271 games) subsets; log alongside 2023 accuracy |
| MODL-05 | Autoresearch experiment loop: agent reads program.md, modifies only train.py, keeps if 2023 val accuracy improves, reverts otherwise | Git-based keep/revert; compound keep rule (>=0.5% improvement OR any improvement + log_loss improvement) |
| MODL-06 | Model must beat both trivial baselines (always-home ~57%, better-record ~60%) on the 2023 validation season | XGBoost with 17 features should comfortably beat these baselines; early stopping + regularization prevent overfitting |
| MODL-07 | TreeSHAP feature importance computed post-training and logged as summary to experiments.jsonl | `shap.TreeExplainer(model).shap_values(X_val)` + `np.abs(shap_values).mean(axis=0)` for global importance ranking |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| xgboost | >=3.2.0 | Gradient boosted tree classifier | Best-in-class for small structured tabular data; native sklearn API; fast training |
| mlflow | >=3.10.0 | Experiment tracking and model registry | Industry standard for ML experiment logging; local file-based mode requires zero infrastructure |
| shap | >=0.51.0 | TreeSHAP feature importance | Exact SHAP values for tree models in milliseconds; both global and local interpretability |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scikit-learn | >=1.5.0 | Metrics (accuracy_score, log_loss, brier_score_loss) | Already a transitive dependency of XGBoost sklearn API |
| joblib | (bundled) | Not for model serialization -- use XGBoost native save_model | Only if needed for parallel computation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| XGBoost native `save_model()` (JSON) | pickle/joblib | Native JSON format has cross-version compatibility guarantee; pickle does not |
| Manual MLflow logging | `mlflow.xgboost.autolog()` | Manual logging gives full control over exactly what is logged; autolog may log unwanted artifacts and lacks custom metric support (log_loss, brier_score, multi-season accuracy) |
| Local file-based MLflow | MLflow tracking server | Local file mode needs zero setup; tracking server is overkill for single-user experiment loop |

**Installation:**
```bash
pip install xgboost>=3.2.0 mlflow>=3.10.0 shap>=0.51.0 scikit-learn>=1.5.0
```

Or add to pyproject.toml dependencies:
```toml
dependencies = [
    # ... existing deps ...
    "xgboost>=3.2.0",
    "mlflow>=3.10.0",
    "shap>=0.51.0",
    "scikit-learn>=1.5.0",
]
```

## Architecture Patterns

### Recommended Project Structure
```
models/
    __init__.py          # Package init
    train.py             # THE file modified during experiments (CLAUDE.md rule)
    baselines.py         # Baseline computation (never modified during experiments)
    program.md           # Experiment queue, current best, dead ends
    artifacts/           # Saved models (XGBoost JSON format)
        best_model.json  # Current best model
    experiments.jsonl    # Append-only experiment log
mlruns/                  # MLflow local tracking directory (auto-created)
```

### Pattern 1: Temporal Split with Tie Exclusion
**What:** Split data by season year and exclude ties from evaluation
**When to use:** Every training run
**Example:**
```python
# Source: project CONTEXT.md locked decisions + XGBoost docs
import pandas as pd
from xgboost import XGBClassifier

def load_and_split(df: pd.DataFrame):
    """Split feature matrix by season with tie exclusion."""
    # Metadata columns to exclude from features
    META_COLS = ["game_id", "season", "week", "gameday", "home_team", "away_team"]
    TARGET = "home_win"

    # Feature columns = everything except meta and target
    feature_cols = [c for c in df.columns if c not in META_COLS + [TARGET]]

    # Temporal split (CLAUDE.md: hardcoded, never shuffle)
    train = df[df["season"].between(2005, 2022)]
    val_2023 = df[df["season"] == 2023]
    val_2022 = df[df["season"] == 2022]
    val_2021 = df[df["season"] == 2021]
    # holdout 2024 is NEVER touched

    # Drop ties (home_win is None/NaN for ties)
    train = train.dropna(subset=[TARGET])
    val_2023 = val_2023.dropna(subset=[TARGET])
    val_2022 = val_2022.dropna(subset=[TARGET])
    val_2021 = val_2021.dropna(subset=[TARGET])

    # Drop week-1 NaN rolling feature rows
    train = train.dropna(subset=feature_cols)
    val_2023 = val_2023.dropna(subset=feature_cols)
    val_2022 = val_2022.dropna(subset=feature_cols)
    val_2021 = val_2021.dropna(subset=feature_cols)

    return train, val_2023, val_2022, val_2021, feature_cols
```

### Pattern 2: Dual Logging (experiments.jsonl + MLflow)
**What:** Every experiment is logged to both the append-only JSONL file and MLflow
**When to use:** After every training run, regardless of keep/revert
**Example:**
```python
# Source: CONTEXT.md locked decision on logging schema
import json
import mlflow
from datetime import datetime, timezone

def log_experiment(
    experiment_id: int,
    params: dict,
    features_used: list[str],
    val_acc_2023: float,
    val_acc_2022: float,
    val_acc_2021: float,
    baseline_home: float,
    baseline_record: float,
    log_loss_val: float,
    brier_score_val: float,
    shap_top5: list[tuple[str, float]],
    keep: bool,
    hypothesis: str,
    prev_best_acc: float,
    model_path: str | None,
):
    """Log experiment to both experiments.jsonl and MLflow."""
    entry = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "params": params,
        "features": features_used,
        "val_accuracy_2023": val_acc_2023,
        "val_accuracy_2022": val_acc_2022,
        "val_accuracy_2021": val_acc_2021,
        "baseline_always_home": baseline_home,
        "baseline_better_record": baseline_record,
        "log_loss": log_loss_val,
        "brier_score": brier_score_val,
        "shap_top5": [{"feature": f, "importance": round(v, 4)} for f, v in shap_top5],
        "keep": keep,
        "hypothesis": hypothesis,
        "prev_best_acc": prev_best_acc,
        "model_path": model_path,
    }

    # Append to JSONL (append-only, CLAUDE.md rule)
    with open("models/experiments.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Log to MLflow
    with mlflow.start_run(run_name=f"exp-{experiment_id:03d}"):
        mlflow.log_params(params)
        mlflow.log_metrics({
            "val_accuracy_2023": val_acc_2023,
            "val_accuracy_2022": val_acc_2022,
            "val_accuracy_2021": val_acc_2021,
            "log_loss": log_loss_val,
            "brier_score": brier_score_val,
            "baseline_always_home": baseline_home,
            "baseline_better_record": baseline_record,
        })
        mlflow.set_tag("keep", str(keep))
        mlflow.set_tag("hypothesis", hypothesis)
        if model_path:
            mlflow.log_artifact(model_path)
```

### Pattern 3: Compound Keep/Revert Decision
**What:** Decision logic that prevents random-walking through noise on a 272-game validation set
**When to use:** After every experiment to decide commit vs revert
**Example:**
```python
# Source: CONTEXT.md locked decision on compound keep rule
def should_keep(
    new_acc: float,
    prev_best_acc: float,
    new_log_loss: float,
    prev_best_log_loss: float,
) -> bool:
    """Compound keep rule from CONTEXT.md.

    Keep if:
      (a) accuracy improves by >= 0.5%, OR
      (b) accuracy improves by any amount AND log_loss also improves
    Otherwise revert.
    """
    acc_improvement = new_acc - prev_best_acc
    log_loss_improved = new_log_loss < prev_best_log_loss

    if acc_improvement >= 0.005:  # >= 0.5 percentage points
        return True
    if acc_improvement > 0 and log_loss_improved:
        return True
    return False
```

### Pattern 4: Better-Record Baseline
**What:** Predict winner as team with more wins so far that season
**When to use:** Computed once in baselines.py before experiments start
**Example:**
```python
# Source: CONTEXT.md locked decision on baseline computation
def better_record_baseline(df: pd.DataFrame) -> float:
    """Better-record baseline accuracy on validation season.

    Predict winner = team with more season wins so far.
    Ties broken by prior season record.
    Home-team fallback when no prior data exists.
    Excludes tied games.
    """
    # home_rolling_win and away_rolling_win represent season win rates
    # so the team with higher rolling win rate has the better record
    val = df.dropna(subset=["home_win"])  # exclude ties
    val = val.dropna(subset=["home_rolling_win", "away_rolling_win"])  # need records

    # Predict home wins when home team has better record
    predictions = (val["home_rolling_win"] > val["away_rolling_win"]).astype(int)

    # For ties in record, could use prior season or home fallback
    tied_record = val["home_rolling_win"] == val["away_rolling_win"]
    predictions[tied_record] = 1  # home team fallback for tied records

    actuals = val["home_win"].astype(int)
    accuracy = (predictions == actuals).mean()
    return accuracy
```

### Anti-Patterns to Avoid
- **Shuffling the temporal split:** NEVER use sklearn train_test_split or any random split. The temporal boundary train=2005-2022, val=2023 is hardcoded and inviolable (CLAUDE.md).
- **Modifying any file except train.py during experiments:** CLAUDE.md explicitly forbids modifying features/build.py, features/definitions.py, or baselines.py during the autoresearch loop.
- **Using result, home_score, or away_score as features:** These are forbidden (CLAUDE.md, definitions.py). The assertion in build.py catches this at feature build time, but never use them in train.py either.
- **Deleting experiments.jsonl entries:** The file is append-only. Reverted experiments stay logged for audit.
- **Using autolog instead of manual logging:** Autolog does not support custom metrics like multi-season accuracy, brier_score, or TreeSHAP top-5. Use manual MLflow logging for full control.
- **Imputing week-1 NaN features with zeros:** Week 1 NaN values mean "no prior games in this season." Imputing with 0 would create misleading features (e.g., 0 win rate implies all losses). Drop these rows instead.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Gradient boosting classifier | Custom tree ensemble | `xgboost.XGBClassifier` | Decades of optimization, GPU support, built-in regularization |
| Feature importance | Manual coefficient analysis | `shap.TreeExplainer` | Exact Shapley values for tree models; polynomial-time algorithm |
| Experiment tracking | Custom CSV/database logger | MLflow | Standard UI, artifact management, run comparison built in |
| Accuracy/loss metrics | Manual metric computation | `sklearn.metrics.accuracy_score`, `log_loss`, `brier_score_loss` | Edge cases handled (e.g., log_loss clipping, multiclass support) |
| Model serialization | pickle/joblib | `model.save_model("path.json")` | XGBoost native JSON format has cross-version stability guarantees |
| JSONL writing | Custom file format | `json.dumps(entry) + "\n"` appended to file | Standard library is sufficient; no need for jsonlines package for append-only writes |

**Key insight:** The complexity in this phase is in the governance infrastructure (keep/revert, dual logging, baseline computation, program.md management), not in the ML modeling itself. XGBoost binary classification with 17 features on 4,639 training rows is a trivially small problem for the algorithm.

## Common Pitfalls

### Pitfall 1: Leakage Through Validation Seasons in Training Set
**What goes wrong:** 2021 and 2022 are used for both training AND overfitting detection. If you accidentally split them out of the training set, the model trains on less data.
**Why it happens:** Confusion between "validation" (2023, used for keep/revert) and "overfitting detection" (2021/2022, evaluated but still in training data).
**How to avoid:** Train on ALL of 2005-2022 inclusive. Evaluate 2021/2022 accuracy by predicting on those subsets AFTER training on the full 2005-2022 set. The 2021/2022 predictions use the same model trained on all data (including 2021/2022 data), so these metrics show how well the model "explains" those seasons, not how well it generalizes. This is intentional: you are looking for relative changes across experiments that signal overfitting, not absolute generalization.
**Warning signs:** Training set size drops below ~4,600 games.

### Pitfall 2: NaN Handling for Week 1 Rows
**What goes wrong:** XGBoost handles NaN natively (treats as missing), so NaN rows do not cause errors. But week-1 rolling features are ALL NaN, meaning the model learns a "week-1 pattern" from situational features alone, which may or may not be desirable.
**Why it happens:** Shift(1) + per-season rolling reset means the first game of each season has no prior data.
**How to avoid:** Drop rows where ALL rolling features are NaN (week-1 rows). This loses ~640 training rows (32 teams x 20 seasons) but avoids conflating "no data" with a learnable pattern. The ~4,000 remaining training rows are still adequate.
**Warning signs:** Model assigns high SHAP importance to `week` or `div_game` disproportionate to rolling features.

### Pitfall 3: Accuracy Noise on Small Validation Set
**What goes wrong:** 272 games means each percentage point is ~2.7 games. A 0.5% improvement is ~1.4 games, dangerously close to random variation.
**Why it happens:** NFL seasons produce only 272 regular-season games (since 2021).
**How to avoid:** The compound keep rule addresses this: require either >=0.5% accuracy improvement OR any improvement backed by log_loss improvement. Log_loss is a continuous metric that is less noisy than binary accuracy.
**Warning signs:** Accuracy oscillates by 0.3-0.5% between experiments while log_loss stays flat or worsens.

### Pitfall 4: XGBoost Default eta=0.3 is Too Aggressive for Small Data
**What goes wrong:** The default learning rate (eta=0.3) with 100 estimators can overfit quickly on 4,000 training rows.
**Why it happens:** XGBoost defaults are tuned for larger datasets (>10K rows).
**How to avoid:** For experiment #1 (baseline), use the XGBoost defaults as-is to establish a starting point. Then in the hyperparameter tuning phase of the experiment queue, reduce eta to 0.05-0.1 and increase n_estimators to 300-500 with early stopping.
**Warning signs:** Training accuracy >> validation accuracy (>10% gap).

### Pitfall 5: Forgetting to Exclude Ties From Both Model AND Baseline Evaluation
**What goes wrong:** Baselines and model are measured on different game sets, making comparison invalid.
**Why it happens:** Ties are rare (~1-2 per season) and easy to forget.
**How to avoid:** Both `baselines.py` and `train.py` must filter `home_win IS NOT NULL` before computing accuracy. Log the exact game count used in each evaluation.
**Warning signs:** Baseline accuracy computed on 272 games but model accuracy on 271 games.

### Pitfall 6: MLflow Run Collisions During Rapid Experimentation
**What goes wrong:** Starting a new MLflow run without ending the previous one creates nested runs or errors.
**Why it happens:** MLflow's context manager (`with mlflow.start_run()`) handles this, but manual `mlflow.start_run()` calls without proper cleanup do not.
**How to avoid:** Always use the context manager pattern: `with mlflow.start_run(run_name=...) as run:`.
**Warning signs:** MLflow UI shows nested runs or runs with 0 metrics.

## Code Examples

### Training a Single Experiment
```python
# Source: XGBoost docs + scikit-learn metrics docs
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
import shap
import numpy as np

def train_and_evaluate(
    X_train, y_train,
    X_val_2023, y_val_2023,
    X_val_2022, y_val_2022,
    X_val_2021, y_val_2021,
    params: dict,
) -> dict:
    """Train XGBoost and evaluate on all validation sets."""
    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        use_label_encoder=False,
        **params,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val_2023, y_val_2023)],
        verbose=False,
    )

    # Predictions and probabilities
    pred_2023 = model.predict(X_val_2023)
    prob_2023 = model.predict_proba(X_val_2023)[:, 1]

    pred_2022 = model.predict(X_val_2022)
    pred_2021 = model.predict(X_val_2021)

    results = {
        "val_accuracy_2023": accuracy_score(y_val_2023, pred_2023),
        "val_accuracy_2022": accuracy_score(y_val_2022, pred_2022),
        "val_accuracy_2021": accuracy_score(y_val_2021, pred_2021),
        "log_loss": log_loss(y_val_2023, prob_2023),
        "brier_score": brier_score_loss(y_val_2023, prob_2023),
    }

    # TreeSHAP feature importance
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_val_2023)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    feature_names = X_val_2023.columns.tolist()
    top5_idx = np.argsort(mean_abs_shap)[-5:][::-1]
    results["shap_top5"] = [
        (feature_names[i], float(mean_abs_shap[i])) for i in top5_idx
    ]

    return results, model
```

### Always-Home Baseline
```python
# Source: CONTEXT.md locked decision
def always_home_baseline(df: pd.DataFrame) -> float:
    """Always predict home team wins. Exclude ties."""
    val = df.dropna(subset=["home_win"])
    return val["home_win"].mean()  # proportion of home wins = accuracy
```

### XGBoost Model Persistence
```python
# Source: XGBoost official docs - save_model (JSON format, cross-version stable)
import os

def save_model(model, experiment_id: int, artifacts_dir: str = "models/artifacts"):
    """Save model using XGBoost native JSON format."""
    os.makedirs(artifacts_dir, exist_ok=True)
    path = os.path.join(artifacts_dir, f"model_exp{experiment_id:03d}.json")
    model.save_model(path)
    return path

def save_best_model(model, artifacts_dir: str = "models/artifacts"):
    """Overwrite best model checkpoint."""
    path = os.path.join(artifacts_dir, "best_model.json")
    model.save_model(path)
    return path
```

### MLflow Setup (Local File-Based)
```python
# Source: MLflow docs - local file tracking
import mlflow

def setup_mlflow():
    """Configure MLflow for local file-based tracking."""
    # Uses ./mlruns directory by default -- no server needed
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("nfl-game-predictor")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| XGBoost pickle serialization | XGBoost native `save_model()` (JSON/UBJSON) | XGBoost 1.0+ | Cross-version compatibility guaranteed; pickle is explicitly warned against in docs |
| `use_label_encoder=True` default | Deprecated; `use_label_encoder=False` | XGBoost 1.6+ | Must explicitly set `use_label_encoder=False` to avoid deprecation warning |
| UBJSON as default save format | UBJSON default since XGBoost 2.1 | XGBoost 2.1 | JSON is still fully supported and more human-readable for debugging |
| MLflow `log_param` (singular) for each param | `log_params` (plural) for dict of params | MLflow 1.0+ | Single call logs all hyperparameters at once |
| `shap.TreeExplainer` with `feature_perturbation` | Default `interventional` approach | SHAP 0.40+ | Default is correct for tree models; no need to specify |
| XGBoost sklearn `n_estimators=100` default | Still 100 in XGBClassifier, but `num_boost_round=10` in native API | XGBoost 3.x | When using sklearn API (XGBClassifier), `n_estimators=100` is the default |

**Deprecated/outdated:**
- `model.get_booster().save_model()`: Use `model.save_model()` directly on the sklearn wrapper (XGBClassifier supports it since XGBoost 1.0+)
- `ntree_limit` parameter in predict: Removed in XGBoost 2.0+, use `iteration_range` instead
- `xgboost.plot_importance()`: Still works but SHAP values are strictly superior for feature importance analysis

## Discretion Decisions (Researcher Recommendations)

### MLflow Tracking Configuration
**Recommendation:** Local file-based tracking (`file:./mlruns`). This is the MLflow default and requires zero infrastructure. The `mlflow ui` command can be run ad-hoc to visualize experiments in a browser at `http://127.0.0.1:5000`. A tracking server is unnecessary for a single-user experiment loop.

### MLflow Experiment Naming and Artifact Storage
**Recommendation:** Experiment name: `"nfl-game-predictor"`. Model artifacts stored at `models/artifacts/` (outside of mlruns) with XGBoost native JSON format. MLflow receives the artifact path via `mlflow.log_artifact()` for cross-referencing but the primary artifact storage is the `models/artifacts/` directory.

### Model Serialization Format
**Recommendation:** XGBoost native `save_model("path.json")`. The official docs explicitly warn that pickle/joblib are NOT stable across XGBoost versions. The native JSON format is human-readable, version-stable, and supported as the primary serialization method.

### TreeSHAP Visualization Approach
**Recommendation:** Do NOT generate plots during the autoresearch loop. Only compute SHAP values, extract top-5 features by mean absolute SHAP value, and log the feature names + importance scores to experiments.jsonl. Visualization is a Phase 5 (Dashboard) concern. Generating matplotlib plots during automated experiments would slow down the loop and produce artifacts nobody reviews in real-time.

### Exact XGBoost Default Parameters for Experiment #1
**Recommendation:** Use the actual XGBoost defaults for the baseline experiment:
```python
{
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.3,   # XGBoost default eta
    "subsample": 1.0,
    "colsample_bytree": 1.0,
    "reg_alpha": 0,
    "reg_lambda": 1,
    "min_child_weight": 1,
    "gamma": 0,
}
```
This establishes a true baseline before any tuning. The experiment queue then varies features first, then adjusts these parameters.

### How NaN Week-1 Rows Are Handled
**Recommendation:** Drop rows where rolling features are all NaN (week 1 of each season). This loses ~640 rows from training (~13.8% of 4,639) but avoids the model learning spurious patterns from all-NaN inputs. The remaining ~4,000 training rows are sufficient for 17 features. Dropping week-1 from validation sets is equally important to keep the evaluation clean. Document the exact row counts before and after dropping in the training script output.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured in pyproject.toml) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/models/ -x -q` |
| Full suite command | `pytest tests/ features/tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODL-01 | Temporal split enforced: train 2005-2022, val 2023, holdout 2024 untouched | unit | `pytest tests/models/test_train.py::test_temporal_split -x` | No -- Wave 0 |
| MODL-02 | Experiment logged to experiments.jsonl and MLflow | unit | `pytest tests/models/test_logging.py::test_dual_logging -x` | No -- Wave 0 |
| MODL-03 | Baselines logged alongside model accuracy | unit | `pytest tests/models/test_baselines.py::test_baseline_computation -x` | No -- Wave 0 |
| MODL-04 | Multi-season accuracy (2021, 2022) logged | unit | `pytest tests/models/test_train.py::test_multi_season_eval -x` | No -- Wave 0 |
| MODL-05 | Autoresearch keep/revert mechanism | unit | `pytest tests/models/test_train.py::test_keep_revert_logic -x` | No -- Wave 0 |
| MODL-06 | Model beats both baselines on 2023 | integration | `pytest tests/models/test_train.py::test_beats_baselines -x` | No -- Wave 0 |
| MODL-07 | TreeSHAP top-5 computed and logged | unit | `pytest tests/models/test_train.py::test_shap_logging -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/models/ -x -q`
- **Per wave merge:** `pytest tests/ features/tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/models/__init__.py` -- package init
- [ ] `tests/models/test_train.py` -- temporal split, multi-season eval, keep/revert logic, beats baselines, SHAP logging
- [ ] `tests/models/test_baselines.py` -- always-home and better-record baseline computation on synthetic data
- [ ] `tests/models/test_logging.py` -- dual logging to JSONL and MLflow
- [ ] `tests/models/conftest.py` -- synthetic feature DataFrames for model tests (reuse pattern from features/tests/conftest.py)

## Open Questions

1. **Exact 2023 regular season tie count**
   - What we know: Ties are rare (1-2 per season). The 2023 season had 272 scheduled games.
   - What's unclear: Exact count of tied games in 2023 to confirm the ~271 non-tie validation size mentioned in CONTEXT.md.
   - Recommendation: Compute dynamically from the data at runtime (`df[df["home_win"].notna()]`) rather than hardcoding. Log the count in every experiment entry.

2. **Better-record baseline tiebreaker using prior season record**
   - What we know: CONTEXT.md specifies ties broken by prior season record.
   - What's unclear: How exactly to access prior season record for the first game of the season (rolling_win would be NaN since it is week 1 of new season).
   - Recommendation: For week 1 games, use the team's final win rate from the prior season. For teams in their first season in the dataset (2005), fall back to home team. Implementation detail for baselines.py.

3. **Early stopping in XGBoost**
   - What we know: XGBoost supports `early_stopping_rounds` parameter in `fit()`.
   - What's unclear: Whether early stopping should be used from experiment #1 or introduced as a hyperparameter variation.
   - Recommendation: Use early stopping from experiment #1 with a generous `early_stopping_rounds=20` and `n_estimators=500`. This finds the right tree count automatically rather than fixing it at 100. The actual number of trees used is logged as a parameter.

## Sources

### Primary (HIGH confidence)
- [XGBoost 3.2.0 official docs](https://xgboost.readthedocs.io/en/stable/) - Parameter defaults, save_model API, parameter tuning guide
- [XGBoost parameter tuning notes](https://xgboost.readthedocs.io/en/stable/tutorials/param_tuning.html) - Overfitting control strategies
- [XGBoost model IO guide](https://xgboost.readthedocs.io/en/stable/tutorials/saving_model.html) - Serialization format stability guarantees
- [MLflow tracking API docs](https://mlflow.org/docs/latest/ml/tracking/tracking-api/) - log_params, log_metrics, log_artifact, start_run
- [MLflow XGBoost integration](https://mlflow.org/docs/latest/python_api/mlflow.xgboost.html) - Autolog compatibility range
- [SHAP TreeExplainer docs](https://shap.readthedocs.io/en/latest/) - XGBoost tree model support
- [scikit-learn metrics](https://scikit-learn.org/stable/modules/model_evaluation.html) - accuracy_score, log_loss, brier_score_loss
- [PyPI xgboost](https://pypi.org/project/xgboost/) - Version 3.2.0, Python >=3.10
- [PyPI mlflow](https://pypi.org/project/mlflow/) - Version 3.10.1, Python >=3.10
- [PyPI shap](https://pypi.org/project/shap/) - Version 0.51.0, Python >=3.11

### Secondary (MEDIUM confidence)
- [XGBoost releases on GitHub](https://github.com/dmlc/xgboost/releases) - Version history verification
- [MLflow tracking quickstart](https://mlflow.org/docs/latest/ml/tracking/quickstart/) - Local file-based tracking confirmation

### Tertiary (LOW confidence)
- None -- all critical findings verified with official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All library versions verified on PyPI, APIs verified in official docs
- Architecture: HIGH - Patterns derived from locked decisions in CONTEXT.md + verified library APIs
- Pitfalls: HIGH - Based on known XGBoost behavior with small datasets and NFL game count constraints from project data
- Validation: MEDIUM - Test structure follows project convention but tests do not yet exist

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable libraries, 30 days)
