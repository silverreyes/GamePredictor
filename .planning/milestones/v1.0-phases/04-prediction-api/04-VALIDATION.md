---
phase: 4
slug: prediction-api
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured in pyproject.toml) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/api/ -x -q` |
| **Full suite command** | `pytest -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/api/ -x -q`
- **After every plan wave:** Run `pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | API-01 | integration | `pytest tests/api/test_predictions.py::test_get_week_predictions -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | API-01 | unit | `pytest tests/api/test_predictions.py::test_week_default_season -x` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | API-01 | integration | `pytest tests/api/test_predictions.py::test_current_week -x` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | API-01 | unit | `pytest tests/api/test_predictions.py::test_offseason -x` | ❌ W0 | ⬜ pending |
| 04-02-01 | 01 | 1 | API-02 | integration | `pytest tests/api/test_predictions.py::test_history -x` | ❌ W0 | ⬜ pending |
| 04-02-02 | 01 | 1 | API-02 | unit | `pytest tests/api/test_predictions.py::test_history_summary -x` | ❌ W0 | ⬜ pending |
| 04-02-03 | 01 | 1 | API-02 | unit | `pytest tests/api/test_predictions.py::test_history_filters -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 01 | 1 | API-03 | integration | `pytest tests/api/test_model.py::test_model_info -x` | ❌ W0 | ⬜ pending |
| 04-03-02 | 01 | 1 | API-03 | unit | `pytest tests/api/test_model.py::test_model_info_baselines -x` | ❌ W0 | ⬜ pending |
| 04-04-01 | 01 | 1 | API-04 | integration | `pytest tests/api/test_model.py::test_reload -x` | ❌ W0 | ⬜ pending |
| 04-04-02 | 01 | 1 | API-04 | unit | `pytest tests/api/test_model.py::test_reload_auth -x` | ❌ W0 | ⬜ pending |
| 04-04-03 | 01 | 1 | API-04 | unit | `pytest tests/api/test_model.py::test_reload_bad_token -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/api/__init__.py` — package init
- [ ] `tests/api/conftest.py` — shared fixtures (TestClient, mock model, test DB)
- [ ] `tests/api/test_predictions.py` — stubs for API-01, API-02
- [ ] `tests/api/test_model.py` — stubs for API-03, API-04
- [ ] `tests/api/test_experiments.py` — stubs for experiments endpoint
- [ ] `httpx` dependency — add to pyproject.toml for TestClient

*pytest is already installed and configured.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Hot-reload doesn't drop in-flight requests | API-04 | Requires concurrent request timing | 1. Start server, 2. Send slow request, 3. Trigger reload mid-request, 4. Verify first request completes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
