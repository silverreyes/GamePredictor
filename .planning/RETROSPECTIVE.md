# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 -- MVP

**Shipped:** 2026-03-18
**Phases:** 6 | **Plans:** 14 | **Execution time:** 1.37 hours

### What Was Built
- Full NFL game prediction pipeline: ingestion, feature engineering, model training, API, dashboard, deployment
- XGBoost classifier at 62.89% accuracy on 2023 validation, beating both trivial baselines
- React dashboard with 4 views (picks, accuracy, experiments, history)
- Docker Compose deployment with 5 services and automated weekly refresh
- 126 commits, ~8,200 LOC (Python + TypeScript + SQL)

### What Worked
- Strict linear phase dependencies meant each phase built cleanly on verified output from the previous
- Autoresearch experiment loop (5 experiments, 2 kept / 3 reverted) efficiently explored the feature/hyperparameter space
- Leakage validation tests as a hard gate prevented data contamination throughout
- Per-phase verification caught the DDL column name mismatch before it became a runtime bug
- Average plan execution time of 5.9 minutes kept momentum high

### What Was Inefficient
- SUMMARY.md one_liner fields were never populated, requiring manual accomplishment extraction at milestone close
- Phase 2 needed an unplanned 02-03 gap closure plan for DDL column names -- could have been caught in plan review
- Nyquist validation files were generated but never fully executed (all 6 phases PARTIAL)
- SITUATIONAL_FEATURES constant in definitions.py drifted from actual column names -- unused but misleading

### Patterns Established
- shift(1) + expanding window as the canonical rolling feature pattern
- Lazy imports in pipeline functions to avoid circular dependencies
- TypeScript types mirroring Pydantic schemas field-for-field as the frontend/backend contract
- Models volume read-only for API, read-write for worker as the deployment access pattern
- Token-protected reload endpoint as the human approval gate

### Key Lessons
1. DDL-to-code column alignment should be verified in plan review, not discovered during verification -- a 2-minute check prevents a gap closure plan
2. Full 17-feature set proved near-optimal; ablation experiments all degraded accuracy -- start with everything and prune, rather than building up incrementally
3. Lower learning rate + early stopping was the single biggest accuracy improvement (Exp 5) -- try regularization before feature engineering
4. Per-season rolling reset is essential for NFL data -- rosters change year to year
5. Caddy + relative URLs eliminated CORS issues for production; hardcoded localhost CORS is fine behind a proxy

### Cost Observations
- Model mix: quality profile (opus for orchestration, sonnet for agents)
- Total execution: ~1.37 hours across 14 plans
- Notable: 3-day end-to-end from project init to shipped milestone is highly efficient for a full-stack ML system

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Execution Time | Phases | Key Change |
|-----------|---------------|--------|------------|
| v1.0 | 1.37 hours | 6 | Initial project -- established all patterns |

### Cumulative Quality

| Milestone | Tests | Verification Score | Tech Debt Items |
|-----------|-------|--------------------|-----------------|
| v1.0 | 102+ passing | 28/28 requirements | 3 (all minor) |

### Top Lessons (Verified Across Milestones)

1. Verify DDL-to-code alignment during planning, not after execution
2. Start with the full feature set and prune -- ablation is cheaper than incremental feature addition
3. Regularization (learning rate, early stopping) before feature engineering for accuracy gains
