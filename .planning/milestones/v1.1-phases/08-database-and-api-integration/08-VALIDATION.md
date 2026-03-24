---
phase: 8
slug: database-and-api-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (via pyproject.toml) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/api/ tests/models/test_predict.py -x -q` |
| **Full suite command** | `pytest tests/ features/tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/api/ tests/models/test_predict.py -x -q`
- **After every plan wave:** Run `pytest tests/ features/tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | API-01 | unit (mock DB) | `pytest tests/models/test_predict.py::test_get_best_spread_experiment -x` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | API-01 | unit | `pytest tests/models/test_predict.py::test_generate_spread_predictions -x` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 1 | API-01 | unit | `pytest tests/models/test_predict.py::test_spread_winner_derivation -x` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 2 | API-02 | unit (TestClient) | `pytest tests/api/test_spreads.py::test_get_spread_week -x` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 2 | API-02 | unit (TestClient) | `pytest tests/api/test_spreads.py::test_spread_503_no_model -x` | ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 2 | API-03 | unit (TestClient) | `pytest tests/api/test_model.py::test_model_info_with_spread -x` | ❌ W0 | ⬜ pending |
| 08-03-02 | 03 | 2 | API-03 | unit (TestClient) | `pytest tests/api/test_model.py::test_model_info_no_spread -x` | ❌ W0 | ⬜ pending |
| 08-04-01 | 04 | 1 | API-04 | unit (TestClient) | `pytest tests/api/test_spreads.py::test_spread_model_loaded -x` | ❌ W0 | ⬜ pending |
| 08-04-02 | 04 | 1 | API-04 | unit (TestClient) | `pytest tests/api/test_spreads.py::test_startup_no_spread_model -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/api/test_spreads.py` — stubs for API-02, API-04 (spread endpoint + startup behavior)
- [ ] `tests/api/conftest.py` update — add spread model mocks to client fixtures
- [ ] `tests/api/test_model.py` update — add spread_model field tests for API-03
- [ ] `tests/models/test_predict.py` update — add spread predict function tests for API-01

*Existing infrastructure covers framework and conftest base — updates needed for spread-specific mocks.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
