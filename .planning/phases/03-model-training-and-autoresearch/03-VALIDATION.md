---
phase: 3
slug: model-training-and-autoresearch
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured in pyproject.toml) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/models/ -x -q` |
| **Full suite command** | `pytest tests/ features/tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/models/ -x -q`
- **After every plan wave:** Run `pytest tests/ features/tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | MODL-01 | unit | `pytest tests/models/test_train.py::test_temporal_split -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | MODL-03 | unit | `pytest tests/models/test_baselines.py::test_baseline_computation -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | MODL-02 | unit | `pytest tests/models/test_logging.py::test_dual_logging -x` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | MODL-04 | unit | `pytest tests/models/test_train.py::test_multi_season_eval -x` | ❌ W0 | ⬜ pending |
| 03-02-03 | 02 | 1 | MODL-07 | unit | `pytest tests/models/test_train.py::test_shap_logging -x` | ❌ W0 | ⬜ pending |
| 03-02-04 | 02 | 1 | MODL-05 | unit | `pytest tests/models/test_train.py::test_keep_revert_logic -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | MODL-06 | integration | `pytest tests/models/test_train.py::test_beats_baselines -x` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 2 | MODL-05 | integration | manual review of experiments.jsonl | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/models/__init__.py` — package init
- [ ] `tests/models/conftest.py` — synthetic feature DataFrames for model tests
- [ ] `tests/models/test_train.py` — temporal split, multi-season eval, keep/revert logic, beats baselines, SHAP logging
- [ ] `tests/models/test_baselines.py` — always-home and better-record baseline computation on synthetic data
- [ ] `tests/models/test_logging.py` — dual logging to JSONL and MLflow

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 5+ logged experiments with iterative improvement | MODL-05, MODL-06 | Requires running actual experiment loop | Review experiments.jsonl for 5+ entries with keep/revert decisions |
| program.md updated with dead ends and suggestions | MODL-05 | Governance artifact, not code | Review models/program.md after experiment session |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
