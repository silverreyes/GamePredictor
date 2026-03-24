---
phase: 11
slug: design-system-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None (build-check + grep audit for CSS/design phase) |
| **Config file** | `frontend/vite.config.ts` (build config) |
| **Quick run command** | `cd frontend && npm run build` |
| **Full suite command** | `cd frontend && npm run build && grep -rEn "(zinc\|blue\|gray\|slate)-[0-9]" src/ --include="*.tsx" --include="*.css"` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run build`
- **After every plan wave:** Run `cd frontend && npm run build` + grep validation for hardcoded classes
- **Before `/gsd:verify-work`:** Full suite must be green (build succeeds + grep returns zero matches)
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | DSGN-01 | manual + build | `cd frontend && npm run build` | N/A | ⬜ pending |
| 11-01-02 | 01 | 1 | DSGN-02 | manual + build | `cd frontend && npm run build` | N/A | ⬜ pending |
| 11-02-01 | 02 | 2 | DSGN-03 | automated grep | `grep -rEn "(zinc\|blue\|gray\|slate)-[0-9]" frontend/src/ --include="*.tsx" --include="*.css"` | N/A | ⬜ pending |
| 11-02-02 | 02 | 2 | DSGN-04 | manual + build | `cd frontend && npm run build` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements — build-check + grep audit provide sufficient automated validation for a CSS/design token phase.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard colors match silverreyes.net warm amber palette | DSGN-01 | Visual color matching cannot be automated without Playwright/Chromatic | Open dashboard in browser, compare background/accent/text colors against silverreyes.net |
| Syne + IBM Plex Mono render correctly, no FOUT | DSGN-02 | Font rendering and FOUT detection require visual inspection | Hard refresh page, verify headings render in Syne and body in IBM Plex Mono with no flash |
| shadcn/ui components display correctly with remapped tokens | DSGN-04 | Component styling requires visual verification across all states | Navigate to pages with buttons, cards, tooltips, dropdowns; verify no broken borders or invisible text |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
