---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Design & Landing Page
status: completed
stopped_at: Completed 14-01-PLAN.md -- v1.2 milestone complete
last_updated: "2026-03-25T03:00:01.547Z"
last_activity: 2026-03-24 -- Phase 14 Plan 01 executed (experiments table fix)
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 5
  completed_plans: 5
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-24)

**Core value:** Pre-game win/loss and point spread predictions that beat trivial baselines, with a polished dashboard for tracking accuracy over time.
**Current focus:** v1.2 milestone complete

## Current Position

Phase: 14 of 14 (Experiments Redesign)
Plan: 1 of 1 in current phase (COMPLETE)
Status: v1.2 milestone complete
Last activity: 2026-03-24 -- Phase 14 Plan 01 executed (experiments table fix)

Progress (v1.2): [====================] 100% (4/4 phases)

## Accumulated Context

### Decisions

Full decision log in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.2]: silverreyes.net design system for Nostradamus -- cohesive brand across subdomains
- [v1.2]: Over/under deferred to v1.3 -- keeps v1.2 scope focused on design refresh
- [v1.2]: Dark-only for v1.2 -- light mode toggle deferred to v1.3
- [v1.2]: Hybrid table+detail layout for experiments -- preserves comparison capability
- [Phase 12]: Pathless layout routes for two-branch route tree (LandingLayout vs AppLayout)
- [Phase 12]: Placeholder landing page with CTA (not redirect) to validate route structure
- [Phase 12]: Sidebar branding shortened to "Nostradamus" for sidebar width constraints
- [Phase 13]: Single-file landing page component with inline blocks array -- no sub-components for static content
- [Phase 13]: Plain divs with bg-secondary/50 for How It Works cards instead of shadcn Card component
- [Phase 13]: Banner image via Vite static import with hard build failure if missing
- [Phase 14]: Removed Collapsible component entirely -- div wrappers inside tbody are fundamentally invalid HTML
- [Phase 14]: Fragment + conditional rendering for table expand/collapse instead of third-party collapsible abstraction

### Pending Todos

None.

### Blockers/Concerns

- Exact silverreyes.net oklch palette values need verification against live site at start of Phase 11
- Experiments hybrid layout approach committed in requirements; no further design ambiguity

## Session Continuity

Last session: 2026-03-25T02:50:00.000Z
Stopped at: Completed 14-01-PLAN.md -- v1.2 milestone complete
Resume file: .planning/phases/14-experiments-redesign/14-01-SUMMARY.md
