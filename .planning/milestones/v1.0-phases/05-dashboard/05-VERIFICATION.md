---
phase: 05-dashboard
verified: 2026-03-17T14:00:00Z
status: human_needed
score: 9/9 must-haves verified
re_verification:
  previous_status: human_needed
  previous_score: 9/9
  gaps_closed: []
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Open http://localhost:5173 after starting API and dev server. Verify This Week's Picks page shows pick cards with predicted winner, win probability percentage, and High/Medium/Low confidence badge for each game."
    expected: "Cards render with team names, highlighted predicted winner at 20px semibold, win probability at 28px semibold, colored left border matching tier (blue/amber/zinc), ConfidenceBadge in bottom of card."
    why_human: "Requires live API + browser to confirm rendering, layout, and confidence tier color coding."
  - test: "Navigate to /accuracy. Verify 3 summary cards render with model record, vs Always-Home, and vs Better-Record comparisons."
    expected: "Cards show correct/total, baseline percentages, and Beating +X% (green) or Behind X% (red) comparison badges. Week-by-week table renders below. If no predictions exist, a friendly 'No Predictions Yet' message appears."
    why_human: "Visual layout and badge color correctness cannot be asserted from static analysis."
  - test: "Navigate to /experiments. Click a column header to sort. Click a row to expand detail."
    expected: "Table sorts on experiment_id and val_accuracy_2023 with ChevronUp/Down icon shown on active column. Expanded row shows params grid, features list, SHAP top-5 bar chart, full hypothesis."
    why_human: "Sort toggle behavior and expandable row animation require interactive browser session."
  - test: "Navigate to /history. Use the Season and Team dropdowns to filter predictions."
    expected: "Page loads with data by default (no ?season= required). Table filters update and URL search params change (e.g. ?season=2023&team=KC). CircleCheck (green) and CircleX (red) icons appear in the Result column."
    why_human: "URL-sync behavior and dropdown interaction require live browser session."
  - test: "Verify sidebar navigation. Click each of the 4 nav items."
    expected: "Active route link has bg-blue-500/10 and text-blue-400 styling. Model status bar at bottom shows 'Exp #N' and 'XX.X% val accuracy'."
    why_human: "Active route highlighting and model status bar data require running app with API."
---

# Phase 5: Dashboard Verification Report

**Phase Goal:** Users can view this week's predictions, track model performance against baselines, compare experiments, and review prediction history through a React dashboard
**Verified:** 2026-03-17
**Status:** human_needed
**Re-verification:** Yes — after two post-initial-verification bug-fix commits

## Re-Verification Summary

Two commits landed after the initial verification (`deef152`). Both were checked for correctness and regressions.

**Commit `3717b51` — `fix(05-02): default history endpoint to latest season with predictions`**

Changed `api/routes/predictions.py` lines 130-140: the `GET /api/predictions/history` endpoint now queries `MAX(season) FROM predictions` instead of `MAX(season) FROM schedules` when no `season` param is provided. Includes a null-check guard that returns an empty `PredictionHistoryResponse` when the predictions table is empty. Fix is correct. No regressions.

**Commit `c4339d6` — `fix(05-02): add empty state handling to AccuracyPage`**

Added a branch in `AccuracyPage.tsx` (lines 88-98) that renders a "No Predictions Yet" `ErrorState` when `historyQuery.data.predictions.length === 0`. Previously the page rendered `SummaryCards` with 0/0 and N/A values, which appeared broken. Fix is correct. No regressions.

All previously-passing truths remain VERIFIED. No new gaps introduced by either commit.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Dashboard shows this week's games with predicted winner, win probability, and confidence tier (DASH-01) | VERIFIED | `ThisWeekPage.tsx` calls `useCurrentPredictions`, renders `PicksGrid` -> `PickCard` with `confidence * 100 toFixed(1)%`, `ConfidenceBadge tier={confidence_tier}`, `text-[28px] font-semibold` probability display |
| 2 | Dashboard shows season accuracy vs always-home and better-record baselines (DASH-02) | VERIFIED | `AccuracyPage.tsx` calls `usePredictionHistory` + `useModelInfo`, passes baselines to `SummaryCards`; empty-predictions guard added (commit c4339d6) prevents broken 0/0 display |
| 3 | Dashboard shows experiment scoreboard with all experiments, 2023 val accuracy, key params, keep/revert status (DASH-03) | VERIFIED | `ExperimentsPage.tsx` calls `useExperiments`, renders `ExperimentTable` with sortable `val_accuracy_2023` column, `Kept`/`Reverted` badges, expandable `ExperimentDetail` rows showing params, features, SHAP top 5 |
| 4 | Dashboard shows historical predictions log with actual outcomes and correct/incorrect indicators (DASH-04) | VERIFIED | `HistoryPage.tsx` calls `usePredictionHistory(season, team)` with URL-synced filters; API now defaults to `MAX(season) FROM predictions` (commit 3717b51) so data loads without explicit season param; `HistoryTable` renders `ResultIndicator` + `actual_winner` column |
| 5 | Frontend project scaffolded with Vite, React, TypeScript, Tailwind v4, shadcn/ui | VERIFIED | `package.json` contains `react`, `react-router`, `@tanstack/react-query`, `tailwindcss ^4`, `shadcn`; all 21 expected component files exist on disk |
| 6 | React Router with 4 routes and persistent sidebar layout | VERIFIED | `App.tsx` uses `BrowserRouter` + layout route wrapping `AppLayout`; routes `/`, `/accuracy`, `/experiments`, `/history` all wired |
| 7 | TanStack Query configured with 5-minute stale time and custom hooks for all API endpoints | VERIFIED | `query-client.ts`: `staleTime: 5 * 60 * 1000`, `refetchOnWindowFocus: false`, `retry: 2`; 4 hooks in `hooks/` each wrap `useQuery` with typed queryKey |
| 8 | TypeScript types match Pydantic response models in api/schemas.py | VERIFIED | All 7 interfaces (`PredictionResponse`, `WeekPredictionsResponse`, `PredictionHistoryResponse`, `HistorySummary`, `ModelInfoResponse`, `ShapFeature`, `ExperimentResponse`) match api/schemas.py field-for-field including optional fields and union types |
| 9 | All pages show loading skeletons and error states with retry buttons on failure | VERIFIED | All 4 pages guard `isLoading` (Skeleton), `isError` (ErrorState with `onRetry`), empty state before rendering content; `AccuracyPage` now also handles empty predictions list |

**Score:** 9/9 truths verified

### Required Artifacts

#### Plan 01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/package.json` | Project dependencies | VERIFIED | Contains `react-router`, `@tanstack/react-query`, `react` |
| `frontend/src/lib/types.ts` | TypeScript types matching API schemas | VERIFIED | All 7 interfaces with correct types; `confidence_tier: "high" \| "medium" \| "low"` present |
| `frontend/src/lib/api.ts` | Centralized API client | VERIFIED | `apiFetch` generic + 5 named exports; `VITE_API_URL` env var with localhost fallback |
| `frontend/src/lib/query-client.ts` | TanStack Query client config | VERIFIED | `new QueryClient` with `staleTime: 5 * 60 * 1000` |
| `frontend/src/App.tsx` | Router + QueryClientProvider + Routes | VERIFIED | `BrowserRouter`, `QueryClientProvider`, `AppLayout` layout route, 4 page routes |
| `frontend/src/components/layout/Sidebar.tsx` | Persistent sidebar with nav + model status | VERIFIED | `NavLink` with active class callback, `useModelInfo` for status bar, Calendar/BarChart3/FlaskConical/History icons, mobile top-nav fallback |
| `frontend/src/components/layout/AppLayout.tsx` | Sidebar + Outlet wrapper | VERIFIED | Imports `Outlet` and `Sidebar`, renders both with responsive margin classes |
| `frontend/src/components/shared/ConfidenceBadge.tsx` | Color-coded confidence tier badge | VERIFIED | `bg-blue-500/20 text-blue-400`, `bg-amber-500/20 text-amber-400`, `bg-zinc-500/20 text-zinc-400` tier styles |
| `frontend/src/components/shared/ErrorState.tsx` | Error card with retry | VERIFIED | `AlertCircle`, `heading`/`body` props, optional `onRetry` button labeled "Try Again" |
| `frontend/src/components/shared/ResultIndicator.tsx` | Green check / red X / pending | VERIFIED | `CircleCheck` (green), `CircleX` (red), `Minus` + "Pending" text for null |

#### Plan 02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/pages/ThisWeekPage.tsx` | Landing page with pick cards grid | VERIFIED | Calls `useCurrentPredictions`, renders `PicksGrid`, handles offseason/loading/error states |
| `frontend/src/components/picks/PickCard.tsx` | Individual game prediction card | VERIFIED | `ConfidenceBadge`, `ResultIndicator`, `border-blue-500`/`border-amber-500`, `text-[28px] font-semibold` probability |
| `frontend/src/components/picks/PicksGrid.tsx` | Responsive grid container | VERIFIED | `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`, maps predictions to PickCard |
| `frontend/src/pages/AccuracyPage.tsx` | Season accuracy with baseline comparison | VERIFIED | `usePredictionHistory` + `useModelInfo`, passes to `SummaryCards`, week-by-week breakdown table; empty state guard added in commit c4339d6 |
| `frontend/src/components/accuracy/SummaryCards.tsx` | 3 summary cards with Beating/Behind | VERIFIED | Model card + 2 comparison cards, `Beating +X%` (green) and `Behind X%` (red) badges |
| `frontend/src/pages/ExperimentsPage.tsx` | Experiment scoreboard | VERIFIED | `useExperiments`, renders `ExperimentTable`, empty state handling |
| `frontend/src/components/experiments/ExperimentTable.tsx` | Sortable table with expandable rows | VERIFIED | `Collapsible`, `ChevronUp`/`ChevronDown` sort icons, `Kept`/`Reverted` badges, `experiment_id` + `val_accuracy_2023` sortable |
| `frontend/src/components/experiments/ExperimentDetail.tsx` | Expandable row detail | VERIFIED | `shap_top5` bar chart, `params` grid, `features` list, full `hypothesis` text |
| `frontend/src/pages/HistoryPage.tsx` | History with URL-synced filters | VERIFIED | `useSearchParams`, `usePredictionHistory`, `HistoryFilters`, `HistoryTable` |
| `frontend/src/components/history/HistoryTable.tsx` | History table with result indicators | VERIFIED | `ResultIndicator`, `ConfidenceBadge`, `predicted_winner`, `actual_winner` columns |
| `frontend/src/components/history/HistoryFilters.tsx` | Season and team filter dropdowns | VERIFIED | `Select` with `All Seasons` and `All Teams` options |

### Key Link Verification

#### Plan 01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `useCurrentPredictions.ts` | `api.ts` | `import fetchCurrentPredictions` | WIRED | `import { fetchCurrentPredictions } from "@/lib/api"` |
| `App.tsx` | `AppLayout.tsx` | layout route element | WIRED | Import + `<Route element={<AppLayout />}>` wrapping all page routes |
| `Sidebar.tsx` | `useModelInfo.ts` | model status bar data | WIRED | `import { useModelInfo }` + called in `ModelStatusBar()` |

#### Plan 02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `ThisWeekPage.tsx` | `/api/predictions/current` | `useCurrentPredictions` hook | WIRED | `useCurrentPredictions()` -> `fetchCurrentPredictions()` -> `GET /api/predictions/current` |
| `AccuracyPage.tsx` | `/api/predictions/history` | `usePredictionHistory` hook | WIRED | `usePredictionHistory()` -> `fetchPredictionHistory()` -> `GET /api/predictions/history` |
| `AccuracyPage.tsx` | `/api/model/info` | `useModelInfo` hook | WIRED | `useModelInfo()` -> `fetchModelInfo()` -> `GET /api/model/info` |
| `ExperimentsPage.tsx` | `/api/experiments` | `useExperiments` hook | WIRED | `useExperiments()` -> `fetchExperiments()` -> `GET /api/experiments` |
| `HistoryPage.tsx` | `/api/predictions/history` | `usePredictionHistory` with URL-synced filters | WIRED | `useSearchParams` reads `season`/`team` from URL -> passed to `usePredictionHistory(season, team)`; API default now queries `MAX(season) FROM predictions` |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| DASH-01 | 05-01-PLAN, 05-02-PLAN | Dashboard displays this week's games with predicted winner, win probability, and confidence tier | SATISFIED | `ThisWeekPage` -> `PicksGrid` -> `PickCard` renders all three fields from `WeekPredictionsResponse` |
| DASH-02 | 05-01-PLAN, 05-02-PLAN | Dashboard displays season accuracy summary vs always-home and better-record baselines | SATISFIED | `AccuracyPage` -> `SummaryCards` renders model record + two baseline comparison cards; empty-predictions case handled gracefully |
| DASH-03 | 05-01-PLAN, 05-02-PLAN | Dashboard displays experiment scoreboard with 2023 val accuracy, key params, keep/revert status | SATISFIED | `ExperimentsPage` -> `ExperimentTable` sortable by val_accuracy_2023, Kept/Reverted badges, `ExperimentDetail` expandable rows |
| DASH-04 | 05-01-PLAN, 05-02-PLAN | Dashboard displays historical predictions log with actual outcome and correct/incorrect highlight | SATISFIED | `HistoryPage` -> `HistoryTable` renders `ResultIndicator` per row, `actual_winner` column, URL-synced season/team filters; API now loads data by default |

All 4 DASH requirements satisfied. DASH-V2-01 through DASH-V2-04 are explicitly future-phase requirements in REQUIREMENTS.md and are not in scope for Phase 5. No orphaned requirements found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `frontend/src/index.css` | CSS @import ordering | `@import url(googleapis)` placed after Tailwind processing directives | Info | Cosmetic only — CSS warning at build time, no functional impact. Build succeeds. |

No TODO/FIXME/placeholder comments found in production source files. No stub implementations found. All `return null` and `return []` occurrences in page files are legitimate data-availability guards (early returns before async data arrives), not stub bodies.

### Human Verification Required

Automated checks confirm all artifacts exist, are substantive (not stubs), and are correctly wired to the API via hooks. The following items require a running browser session to confirm visual and interactive correctness per DASH requirements.

#### 1. This Week's Picks — Visual layout (DASH-01)

**Test:** Start API (`python -m uvicorn api.main:app --reload`) and dev server (`cd frontend && npm run dev`). Navigate to `http://localhost:5173`.
**Expected:** Pick cards render in a 3-column grid with team names, highlighted predicted winner (20px semibold), win probability (28px semibold), confidence tier colored left border (blue/amber/zinc), and High/Medium/Low badge at bottom of each card. If games have results, green CircleCheck or red CircleX appears in the top-right corner of cards.
**Why human:** CSS class rendering and responsive grid layout require a real browser.

#### 2. Season Accuracy — Baseline comparison badges (DASH-02)

**Test:** Navigate to `/accuracy`.
**Expected:** Three cards display with model record (correct/total), always-home baseline %, and better-record baseline %. Green "Beating +X%" badge appears when model accuracy exceeds baseline; red "Behind X%" badge when it does not. Week-by-week table renders below. If no predictions exist, a friendly "No Predictions Yet" message appears instead of broken 0/0 cards.
**Why human:** Badge color styling (green vs red) and table row layout require visual confirmation.

#### 3. Experiment Scoreboard — Sort and expand interaction (DASH-03)

**Test:** Navigate to `/experiments`. Click the "2023 Val Acc" column header. Then click any experiment row.
**Expected:** Table re-sorts with ChevronUp or ChevronDown icon shown next to the active column header. Clicking the same header again reverses sort direction. Clicking a row expands a detail section showing: full hypothesis text, params key-value grid, comma-separated features list, SHAP top-5 bar chart with proportional blue bars.
**Why human:** Sort toggle behavior, expand/collapse animation, and SHAP bar proportionality require live interaction.

#### 4. Prediction History — URL-synced filters (DASH-04)

**Test:** Navigate to `/history` with no query params.
**Expected:** Page loads with prediction data by default (no `?season=` required — API now defaults to latest season with predictions). Selecting a season changes URL to `/history?season=2023`. Selecting a team adds `&team=KC`. Result column shows green CircleCheck for correct predictions and red CircleX for incorrect ones.
**Why human:** URL mutation behavior and filter-driven refetch require live browser session with running API.

#### 5. Sidebar navigation and model status bar

**Test:** Click each of the 4 sidebar nav items in sequence.
**Expected:** Active route link has blue-tinted background (`bg-blue-500/10`) and blue text (`text-blue-400`). Inactive links show muted text. Model status bar at bottom of sidebar shows "Exp #N" and "XX.X% val accuracy" from the `/api/model/info` endpoint.
**Why human:** Active route highlighting via NavLink `className` callback and dynamic model status data require live app.

### Gaps Summary

No gaps found. This is a re-verification following two post-initial-verification bug-fix commits. Both commits are correct and improve goal achievement without introducing regressions:

- Commit `3717b51` fixes the history endpoint default so DASH-04 works without requiring an explicit `?season=` parameter, which is the expected behavior when a user first lands on `/history`.
- Commit `c4339d6` prevents a visually broken 0/0 state on `/accuracy` when no predictions have been generated, improving the DASH-02 user experience.

All 9 observable truths remain VERIFIED. All 21 required artifacts exist and are substantive. All 8 key links are wired end-to-end. The 4 DASH requirements are fully satisfied. No regressions introduced by the two new commits.

The only remaining items are the 5 human verification checks for visual and interactive correctness, unchanged from the initial verification.

---

_Verified: 2026-03-17_
_Verifier: Claude (gsd-verifier)_
