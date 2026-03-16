---
phase: 2
slug: feature-engineering
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/features/ -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/features/ -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | FEAT-01 | unit | `pytest tests/features/test_rolling.py -q` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | FEAT-02 | unit | `pytest tests/features/test_rolling.py -q` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | FEAT-03 | unit | `pytest tests/features/test_situational.py -q` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | FEAT-04 | unit | `pytest tests/features/test_build.py -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | FEAT-05 | integration | `pytest tests/features/test_leakage.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/features/test_rolling.py` — stubs for FEAT-01, FEAT-02
- [ ] `tests/features/test_situational.py` — stubs for FEAT-03
- [ ] `tests/features/test_build.py` — stubs for FEAT-04
- [ ] `tests/features/test_leakage.py` — stubs for FEAT-05

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Feature matrix covers all 20 seasons without gaps | FEAT-04 | Requires live DB with ingested data | Run `SELECT season, COUNT(*) FROM game_features GROUP BY season ORDER BY season` and verify 20 rows |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
