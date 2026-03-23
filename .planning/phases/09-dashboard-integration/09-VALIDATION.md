---
phase: 9
slug: dashboard-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None (frontend has no test framework — consistent with Phases 1-8) |
| **Config file** | None |
| **Quick run command** | `cd frontend && npm run build` |
| **Full suite command** | `cd frontend && npm run build && npm run lint` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run build`
- **After every plan wave:** Run `cd frontend && npm run build && npm run lint`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | DASH-01 | build | `cd frontend && npm run build` | N/A | ⬜ pending |
| 09-01-02 | 01 | 1 | DASH-01 | build | `cd frontend && npm run build` | N/A | ⬜ pending |
| 09-02-01 | 02 | 1 | DASH-02 | build | `cd frontend && npm run build` | N/A | ⬜ pending |
| 09-02-02 | 02 | 1 | DASH-03 | build | `cd frontend && npm run build` | N/A | ⬜ pending |
| 09-03-01 | 03 | 2 | DASH-04 | build | `cd frontend && npm run build` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No test framework to install — frontend validation is TypeScript build + manual visual inspection (established project pattern).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PickCards display predicted spread below confidence % | DASH-01 | Visual rendering verification | Load ThisWeekPage with spread data in DB, verify spread line appears below confidence |
| Spread MAE card appears on AccuracyPage | DASH-02 | Visual rendering verification | Load AccuracyPage, verify Spread Model section shows MAE card |
| Post-game cards show actual margin and error | DASH-03 | Visual rendering verification | Load ThisWeekPage with completed games, verify "Actual +X (off by Y)" appears with color coding |
| Agreement breakdown card on AccuracyPage | DASH-04 | Visual rendering verification | Load AccuracyPage, verify agreement/disagreement counts match expected values |
| Spread section hidden when no spread model | ALL | Conditional rendering | Unload spread model, verify cards look exactly like v1.0 on both pages |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
