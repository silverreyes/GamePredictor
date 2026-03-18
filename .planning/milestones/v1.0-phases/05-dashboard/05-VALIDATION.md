---
phase: 5
slug: dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual browser verification + Vite/TypeScript build check |
| **Config file** | `frontend/vite.config.ts` (TypeScript strict mode via tsconfig.json) |
| **Quick run command** | `cd frontend && npm run build` |
| **Full suite command** | `cd frontend && npm run build` + manual walkthrough of all 4 pages |
| **Estimated runtime** | ~10 seconds (build) + ~5 minutes (manual walkthrough) |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run build`
- **After every plan wave:** Run `cd frontend && npm run build` + manual page walkthrough
- **Before `/gsd:verify-work`:** Full build must succeed, all 4 pages render with API data
- **Max feedback latency:** 10 seconds (build check)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | DASH-01 | build | `cd frontend && npm run build` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | DASH-02 | build | `cd frontend && npm run build` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | DASH-03 | build | `cd frontend && npm run build` | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 1 | DASH-04 | build | `cd frontend && npm run build` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/` directory — entire project scaffolding (React + Vite + TypeScript)
- [ ] `frontend/package.json` — all dependencies installed (react-router, @tanstack/react-query, shadcn/ui components)
- [ ] `frontend/src/lib/types.ts` — TypeScript types matching api/schemas.py
- [ ] `frontend/tsconfig.json` — strict mode with path aliases configured

*Note: No automated test framework (jest/vitest) is in scope for Phase 5 v1. Validation relies on TypeScript build checks and manual browser verification.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Pick cards display with winner, probability, tier | DASH-01 | Visual rendering requires browser | Open `/`, verify pick cards render with data from GET /api/predictions/current |
| Season accuracy with baseline comparison | DASH-02 | Visual layout of summary cards | Open `/accuracy`, verify 3 summary cards show model record and baseline badges |
| Experiment scoreboard with sortable table | DASH-03 | Interactive sorting and expandable rows | Open `/experiments`, verify table renders, click column headers to sort, expand a row |
| Historical predictions with correct/incorrect icons | DASH-04 | Visual indicators and filter interaction | Open `/history`, verify CircleCheck/CircleX icons, test season and team filter dropdowns |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
