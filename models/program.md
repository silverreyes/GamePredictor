# Experiment Program

## Baselines (Fixed Reference)
- Always-home accuracy (2023): 55.51%
- Better-record accuracy (2023): 58.20%
- Always-home game count (2023): 272
- Better-record game count (2023, excl. ties + NaN week-1): 256

## Current Best
| Season | Accuracy |
|--------|----------|
| 2021   | --       |
| 2022   | --       |
| 2023   | --       |
| Log Loss | --     |
| Brier Score | --  |

Best experiment: none yet

## Termination Conditions
1. Stop after 20 experiments total
2. Stop if 3 consecutive experiments show <0.3% improvement
3. Stop if 2021/2022 accuracy degrades while 2023 improves (overfitting signal)

## Experiment Queue

Queue order: vary the signal first, then tune the noise.

### Phase 1: Baseline (Experiment 1)
- [ ] **Exp 1**: XGBoost with all 17 features, default hyperparameters
  - n_estimators=100, max_depth=6, learning_rate=0.3, subsample=1.0, colsample_bytree=1.0, reg_alpha=0, reg_lambda=1, min_child_weight=1, gamma=0
  - Hypothesis: Establish baseline accuracy with default XGBoost on full feature set

### Phase 2: Feature Ablation (Experiments 2-4)
NOTE: These are all drop experiments (one-directional ablation). They test whether removing features improves accuracy, but don't test whether adding features (e.g., different rolling windows, feature interactions) would help. If all ablations hurt accuracy, the conclusion is that the full feature set is already near-optimal -- worth noting but not a flaw in the queue.
- [ ] **Exp 2**: Drop turnover features (turnovers_committed, turnovers_forced, turnover_diff -- 6 columns removed)
  - Hypothesis: Turnovers may be noisy game-to-game; removing may reduce overfitting
- [ ] **Exp 3**: Drop EPA features (off_epa_per_play, def_epa_per_play -- 4 columns removed)
  - Hypothesis: EPA may overlap with point_diff; simpler model may generalize better
- [ ] **Exp 4**: Drop situational features (home_rest, away_rest, div_game -- 3 columns removed)
  - Hypothesis: Rest days and divisional flag may add noise without predictive value

### Phase 3: Hyperparameter Tuning (Experiments 5-7)
- [ ] **Exp 5**: Reduce learning_rate to 0.1, increase n_estimators to 300, add early_stopping_rounds=20
  - Hypothesis: Slower learning with more trees and early stopping prevents overfitting on small dataset
- [ ] **Exp 6**: Reduce max_depth to 3 (from 6)
  - Hypothesis: Shallower trees generalize better on 4000-row dataset
- [ ] **Exp 7**: Set subsample=0.8, colsample_bytree=0.8
  - Hypothesis: Stochastic boosting reduces overfitting via ensemble diversity

### Phase 4: Regularization (Experiments 8-10)
- [ ] **Exp 8**: Increase reg_lambda to 5
  - Hypothesis: L2 regularization constrains leaf weights on small dataset
- [ ] **Exp 9**: Add reg_alpha=0.1 (L1 regularization)
  - Hypothesis: L1 sparsity may zero out noise features
- [ ] **Exp 10**: Set min_child_weight=5
  - Hypothesis: Larger minimum leaf size prevents learning from rare patterns

## Dead Ends (Do Not Retry)
(none yet)

## Session Log
(none yet)
