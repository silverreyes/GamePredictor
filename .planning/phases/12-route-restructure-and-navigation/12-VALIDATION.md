---
phase: 12
slug: route-restructure-and-navigation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None -- no frontend test framework exists |
| **Config file** | None |
| **Quick run command** | `cd frontend && npm run build` |
| **Full suite command** | `cd frontend && npm run build && npm run lint` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run build`
- **After every plan wave:** Run `cd frontend && npm run build && npm run lint`
- **Before `/gsd:verify-work`:** Full suite must be green + manual verification of all 5 routes
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | NAV-01 | manual | Visual: sidebar shows Home icon+label, clicking navigates to `/` | N/A | ⬜ pending |
| 12-01-02 | 01 | 1 | NAV-02 | smoke | `cd frontend && npm run build` + manual navigate to `/this-week` | N/A | ⬜ pending |
| 12-01-03 | 01 | 1 | NAV-03 | smoke | `cd frontend && npm run build` + manual navigate to `/accuracy`, `/experiments`, `/history` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. `npm run build` provides TypeScript type-checking that catches broken imports, missing components, and route errors. Manual route verification covers the rest.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `/` renders full-width page with no sidebar | NAV-02, SC-1 | Layout verification requires visual inspection | Navigate to `/`, confirm no sidebar or dashboard chrome visible |
| `/this-week` renders with sidebar | NAV-02, SC-2 | Layout verification requires visual inspection | Navigate to `/this-week`, confirm sidebar visible and This Week content renders |
| Home tab active state | NAV-01, SC-3 | Active-state highlighting requires visual inspection | Click Home in sidebar, confirm it highlights; navigate to dashboard page, confirm Home is NOT highlighted |
| All existing routes work | NAV-03, SC-4 | Route verification requires navigation | Navigate to `/accuracy`, `/experiments`, `/history` — all render with sidebar |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
