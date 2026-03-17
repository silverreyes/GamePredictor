---
phase: 05-dashboard
plan: 01
subsystem: ui
tags: [react, vite, tailwind, shadcn, tanstack-query, react-router, typescript]

# Dependency graph
requires:
  - phase: 04-prediction-api
    provides: FastAPI endpoints and Pydantic response models (api/schemas.py)
provides:
  - React frontend project with Vite + Tailwind v4 + shadcn/ui
  - TypeScript types mirroring all API Pydantic schemas
  - Centralized API client with 5 fetch functions
  - TanStack Query client with 4 custom hooks
  - App shell with sidebar navigation and React Router (4 routes)
  - Shared UI components (ConfidenceBadge, ErrorState, ResultIndicator)
affects: [05-dashboard]

# Tech tracking
tech-stack:
  added: [react, react-dom, vite, tailwindcss, "@tailwindcss/vite", shadcn, "@tanstack/react-query", react-router, lucide-react, class-variance-authority, clsx, tailwind-merge]
  patterns: [centralized API client with typed fetch, TanStack Query hooks per endpoint, layout route with Outlet, NavLink active highlighting]

key-files:
  created:
    - frontend/package.json
    - frontend/vite.config.ts
    - frontend/src/lib/types.ts
    - frontend/src/lib/api.ts
    - frontend/src/lib/query-client.ts
    - frontend/src/hooks/useCurrentPredictions.ts
    - frontend/src/hooks/usePredictionHistory.ts
    - frontend/src/hooks/useModelInfo.ts
    - frontend/src/hooks/useExperiments.ts
    - frontend/src/components/layout/Sidebar.tsx
    - frontend/src/components/layout/AppLayout.tsx
    - frontend/src/components/shared/ConfidenceBadge.tsx
    - frontend/src/components/shared/ErrorState.tsx
    - frontend/src/components/shared/ResultIndicator.tsx
    - frontend/src/pages/ThisWeekPage.tsx
    - frontend/src/pages/AccuracyPage.tsx
    - frontend/src/pages/ExperimentsPage.tsx
    - frontend/src/pages/HistoryPage.tsx
    - frontend/src/App.tsx
  modified:
    - frontend/index.html
    - frontend/src/index.css
    - frontend/tsconfig.json
    - frontend/tsconfig.app.json

key-decisions:
  - "Downgraded Vite 8 to 7 for @tailwindcss/vite peer dependency compatibility"
  - "Removed Geist font in favor of Inter per UI-SPEC design system"
  - "Removed nested .git directory created by Vite scaffolding to avoid submodule issues"

patterns-established:
  - "API client: apiFetch<T> generic with typed wrapper functions per endpoint"
  - "Hooks: one custom hook per API endpoint wrapping useQuery with typed queryKey"
  - "Layout: AppLayout with Sidebar + Outlet, responsive breakpoints at md (768px) and lg (1024px)"
  - "Shared components: stateless display components accepting typed props"

requirements-completed: [DASH-01, DASH-02, DASH-03, DASH-04]

# Metrics
duration: 9min
completed: 2026-03-17
---

# Phase 5 Plan 1: Frontend Foundation Summary

**React + Vite + Tailwind v4 + shadcn/ui app shell with typed API client, TanStack Query hooks, sidebar navigation, and shared components for NFL Predictor dashboard**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-17T14:53:39Z
- **Completed:** 2026-03-17T15:03:00Z
- **Tasks:** 2
- **Files modified:** 39

## Accomplishments
- Full React frontend project scaffolded with Vite, TypeScript, Tailwind v4, and 8 shadcn/ui components
- TypeScript interfaces match all 7 Pydantic response models from api/schemas.py exactly
- Centralized API client with typed fetch functions for all 5 API endpoints
- TanStack Query configured (5min stale time, no window refocus, retry 2) with 4 custom hooks
- Persistent sidebar with 4 NavLink items, active route highlighting, and model status bar
- 3 shared components (ConfidenceBadge, ErrorState, ResultIndicator) ready for page views
- 4 routed placeholder pages with browser tab titles per UI-SPEC copywriting contract

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold frontend project with Vite + shadcn/ui + dependencies** - `998c825` (feat)
2. **Task 2: Create types, API client, query hooks, layout shell, and shared components** - `a53f3ec` (feat)

## Files Created/Modified
- `frontend/package.json` - Project dependencies (react, react-router, tanstack-query, tailwind, shadcn)
- `frontend/vite.config.ts` - Vite config with React plugin, Tailwind v4 plugin, and @/ path alias
- `frontend/tsconfig.json` - Root tsconfig with @/ path alias
- `frontend/tsconfig.app.json` - App tsconfig with @/ path alias and strict mode
- `frontend/index.html` - HTML template with dark mode class and NFL Predictor title
- `frontend/src/index.css` - Tailwind v4 with shadcn theme variables, Inter font, dark mode
- `frontend/src/main.tsx` - React entry point with StrictMode
- `frontend/src/App.tsx` - BrowserRouter + QueryClientProvider + Routes with AppLayout
- `frontend/src/lib/types.ts` - TypeScript interfaces for all 7 API response models
- `frontend/src/lib/api.ts` - Generic apiFetch + 5 typed API fetch functions
- `frontend/src/lib/query-client.ts` - QueryClient with 5min stale, no refetch, retry 2
- `frontend/src/lib/utils.ts` - cn() utility from shadcn/ui
- `frontend/src/hooks/useCurrentPredictions.ts` - Hook for current week predictions
- `frontend/src/hooks/usePredictionHistory.ts` - Hook for prediction history with filters
- `frontend/src/hooks/useModelInfo.ts` - Hook for model info
- `frontend/src/hooks/useExperiments.ts` - Hook for experiments list
- `frontend/src/components/layout/Sidebar.tsx` - Persistent sidebar with nav items + model status
- `frontend/src/components/layout/AppLayout.tsx` - Sidebar + Outlet wrapper with responsive margins
- `frontend/src/components/shared/ConfidenceBadge.tsx` - Color-coded badge for high/medium/low tiers
- `frontend/src/components/shared/ErrorState.tsx` - Error card with icon, heading, body, retry button
- `frontend/src/components/shared/ResultIndicator.tsx` - Green check / red X / pending indicator
- `frontend/src/pages/ThisWeekPage.tsx` - Placeholder page for This Week's Picks
- `frontend/src/pages/AccuracyPage.tsx` - Placeholder page for Season Accuracy
- `frontend/src/pages/ExperimentsPage.tsx` - Placeholder page for Experiment Scoreboard
- `frontend/src/pages/HistoryPage.tsx` - Placeholder page for Prediction History
- `frontend/src/components/ui/*.tsx` - 8 shadcn components (card, table, badge, skeleton, select, collapsible, separator, button)

## Decisions Made
- Downgraded Vite 8 to 7 because @tailwindcss/vite requires peer vite <=7 (Vite 8 too new)
- Replaced Geist font with Inter across the shadcn theme variables to match UI-SPEC design system
- Removed nested .git directory that Vite scaffolding created inside frontend/ to prevent git submodule issues
- Used @vitejs/plugin-react v4 (compatible with Vite 7) instead of v6 (requires Vite 8)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Vite 8 incompatible with @tailwindcss/vite**
- **Found during:** Task 1 (Tailwind CSS installation)
- **Issue:** @tailwindcss/vite requires peer vite "^5.2.0 || ^6 || ^7" but create-vite scaffolded Vite 8
- **Fix:** Downgraded vite to ^7 and @vitejs/plugin-react to ^4
- **Files modified:** frontend/package.json
- **Verification:** npm install succeeds, npm run build exits 0
- **Committed in:** 998c825 (Task 1 commit)

**2. [Rule 3 - Blocking] Nested .git directory preventing file staging**
- **Found during:** Task 1 (git commit)
- **Issue:** Vite scaffolding created frontend/.git, causing git to treat frontend/ as a submodule
- **Fix:** Removed frontend/.git directory so files could be staged individually
- **Files modified:** (none - deleted .git directory)
- **Verification:** git add succeeds, files appear in staged status
- **Committed in:** 998c825 (Task 1 commit)

**3. [Rule 3 - Blocking] shadcn init required tsconfig.json path alias**
- **Found during:** Task 1 (shadcn initialization)
- **Issue:** shadcn init checks root tsconfig.json for import alias, not tsconfig.app.json
- **Fix:** Added baseUrl and paths to both tsconfig.json and tsconfig.app.json
- **Files modified:** frontend/tsconfig.json, frontend/tsconfig.app.json
- **Verification:** npx shadcn@latest init succeeds
- **Committed in:** 998c825 (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (3 blocking issues)
**Impact on plan:** All fixes necessary to unblock scaffolding. No scope creep.

## Issues Encountered
- CSS @import order warning during build (Google Fonts @import after Tailwind processing) - cosmetic only, build succeeds, no functional impact

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Frontend foundation complete with all infrastructure for building page views
- Plan 05-02 can build all 4 page views using the types, hooks, and shared components created here
- API server must be running on localhost:8000 for live data (Vite dev server proxies to it)

## Self-Check: PASSED

- All 25 key files verified present on disk
- Both task commits (998c825, a53f3ec) verified in git log
- Build verification: `npm run build` exits 0

---
*Phase: 05-dashboard*
*Completed: 2026-03-17*
