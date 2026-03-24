---
phase: 12-route-restructure-and-navigation
plan: "01"
subsystem: ui
tags: [react-router, routing, navigation, sidebar, layout]

# Dependency graph
requires:
  - phase: 11-design-system-foundation
    provides: "Design tokens (bg-background, text-foreground, font-display, bg-primary), Syne + IBM Plex Mono fonts"
provides:
  - "Two-branch route tree: LandingLayout for / and AppLayout for dashboard routes"
  - "LandingLayout component: full-width, no sidebar wrapper"
  - "LandingPage placeholder: heading, subtext, CTA linking to /this-week"
  - "Sidebar Home nav item linking to / with active-state end prop"
  - "This Week route moved from / to /this-week"
  - "Sidebar branding updated to Nostradamus"
affects: [13-landing-page-content, future-navigation-phases]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pathless layout routes for layout branching (React Router v7)"
    - "LandingLayout vs AppLayout two-branch pattern"

key-files:
  created:
    - "frontend/src/components/layout/LandingLayout.tsx"
    - "frontend/src/pages/LandingPage.tsx"
  modified:
    - "frontend/src/App.tsx"
    - "frontend/src/components/layout/Sidebar.tsx"

key-decisions:
  - "Used pathless layout routes (not conditional rendering) for two-branch route tree"
  - "Placeholder landing page with CTA (not redirect to /this-week) to validate route structure"
  - "Sidebar branding shortened to 'Nostradamus' (not 'NFL Nostradamus') for sidebar width constraints"

patterns-established:
  - "Layout branching: pathless Route element wraps grouped routes sharing a layout"
  - "NavLink end prop on / routes to prevent false active-state matching"

requirements-completed: [NAV-01, NAV-02, NAV-03]

# Metrics
duration: 3min
completed: 2026-03-24
---

# Phase 12 Plan 01: Route Restructure and Navigation Summary

**Two-branch route tree with LandingLayout (full-width, no sidebar) at / and AppLayout (sidebar + dashboard) at /this-week, /accuracy, /experiments, /history, plus Home nav item and Nostradamus branding**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-24T19:19:35Z
- **Completed:** 2026-03-24T19:22:35Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Created two-branch route tree: LandingLayout wrapping / index route, AppLayout wrapping all dashboard routes
- Created LandingLayout component (full-width, no sidebar) and LandingPage placeholder with "NFL Nostradamus" heading and CTA
- Added Home nav item as first sidebar entry linking to / with correct active-state handling
- Moved This Week from / to /this-week and updated sidebar branding to "Nostradamus"

## Task Commits

Each task was committed atomically:

1. **Task 1: Create LandingLayout, LandingPage, and restructure App.tsx route tree** - `9f7f9a3` (feat)
2. **Task 2: Update Sidebar navigation items and branding** - `23a475a` (feat)

## Files Created/Modified
- `frontend/src/components/layout/LandingLayout.tsx` - Full-width layout wrapper with Outlet, no sidebar
- `frontend/src/pages/LandingPage.tsx` - Placeholder landing page with heading, subtext, and CTA to /this-week
- `frontend/src/App.tsx` - Two-branch route tree: LandingLayout for /, AppLayout for dashboard routes
- `frontend/src/components/layout/Sidebar.tsx` - Added Home nav item, updated This Week path, renamed branding to Nostradamus

## Decisions Made
- Used pathless layout routes (React Router v7 pattern) instead of conditional rendering for layout branching -- cleaner separation, declarative
- Created a real placeholder page at / instead of redirecting to /this-week -- validates route structure works and provides visual confirmation of no-sidebar layout
- Shortened sidebar branding to "Nostradamus" (not "NFL Nostradamus") -- fits sidebar width constraints, Phase 13 landing page will show full name

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all changes compiled and built on first attempt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- LandingLayout and LandingPage are ready for Phase 13 to replace placeholder content with real landing page hero, features, and CTA sections
- Route tree supports adding new routes under either layout branch
- All 5 navigation items (Home, This Week, Accuracy, Experiments, History) render with correct paths and active-state behavior

## Self-Check: PASSED

- All 4 source files exist (LandingLayout.tsx, LandingPage.tsx, App.tsx, Sidebar.tsx)
- Commit 9f7f9a3 (Task 1) verified in git log
- Commit 23a475a (Task 2) verified in git log
- SUMMARY.md exists at expected path

---
*Phase: 12-route-restructure-and-navigation*
*Completed: 2026-03-24*
