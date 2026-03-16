---
phase: 1
slug: data-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | None — Wave 0 creates pyproject.toml [tool.pytest] |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds (unit), ~60 seconds (with integration) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DATA-01 | integration | `pytest tests/test_ingestion.py::test_pbp_ingestion -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | DATA-02 | integration | `pytest tests/test_ingestion.py::test_schedule_ingestion -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | DATA-03 | unit | `pytest tests/test_transforms.py::test_team_normalization -x` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | DATA-04 | unit | `pytest tests/test_validators.py::test_validation_failures -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — project config with [tool.pytest] section
- [ ] `tests/__init__.py` — test package init
- [ ] `tests/conftest.py` — shared fixtures (test DB engine, sample DataFrames)
- [ ] `tests/test_transforms.py` — team normalization, column selection, preseason filtering
- [ ] `tests/test_validators.py` — game count validation, schema drift detection
- [ ] `tests/test_ingestion.py` — integration tests (requires running PostgreSQL)
- [ ] Framework install: `pip install pytest` — if not already in dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker PostgreSQL starts cleanly | DATA-01 | Requires Docker daemon | Run `docker compose up -d`, verify `docker compose ps` shows healthy |
| Stdout summary table readable | DATA-04 | Visual formatting check | Run `python -m data.ingest --seasons 2023` and inspect stdout table |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
