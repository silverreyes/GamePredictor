---
phase: 05-dashboard
plan: 02
subsystem: ui
tags: [react, typescript, shadcn, tanstack-query, dashboard-pages, seed-data]

# Dependency graph
requires:
  - phase: 05-dashboard
    provides: React frontend foundation with types, hooks, layout shell, and shared components (Plan 01)
  - phase: 04-prediction-api
    provides: FastAPI endpoints for predictions, history, model info, and experiments
provides:
  - 4 complete dashboard pages (This Week, Accuracy, Experiments, History)
  - Pick card components with confidence tier badges and result indicators
  - Sortable experiment table with expandable detail rows
  - Filterable prediction history with URL-synced season/team dropdowns
  - Empty state handling for all pages when no predictions exist
  - Seed script for populating predictions table with development data
affects: [05-dashboard, 06-pipeline-and-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns: [empty state handling distinct from loading/error states, seed script for development data, URL-synced filter state via useSearchParams]

key-files:
  created:
    - frontend/src/components/picks/PickCard.tsx
    - frontend/src/components/picks/PicksGrid.tsx
    - frontend/src/components/accuracy/SummaryCards.tsx
    - frontend/src/components/experiments/ExperimentTable.tsx
    - frontend/src/components/experiments/ExperimentDetail.tsx
    - frontend/src/components/history/HistoryTable.tsx
    - frontend/src/components/history/HistoryFilters.tsx
    - scripts/seed_predictions.py
  modified:
    - frontend/src/pages/ThisWeekPage.tsx
    - frontend/src/pages/AccuracyPage.tsx
    - frontend/src/pages/ExperimentsPage.tsx
    - frontend/src/pages/HistoryPage.tsx

key-decisions:
  - "Added empty state handling to AccuracyPage for graceful display when no predictions exist"
  - "Created seed_predictions script to generate 2023 validation predictions for dashboard development"
  - "predictions table created via DDL at runtime since it was missing from database"

patterns-established:
  - "Empty state pattern: check data.predictions.length === 0 after isLoading/isError guards, show ErrorState with informational message"
  - "Seed data pattern: scripts/seed_predictions.py loads model, builds features, runs inference on completed games, stores with actual outcomes"

requirements-completed: [DASH-01, DASH-02, DASH-03, DASH-04]

# Metrics
duration: 10min
completed: 2026-03-17
---

# Phase 5 Plan 2: Dashboard Page Views Summary

**4 dashboard pages with pick cards, accuracy comparison, sortable experiment table, filterable history, empty state handling, and seed data script for 256 predictions**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-17T15:07:53Z
- **Completed:** 2026-03-17T15:18:15Z
- **Tasks:** 3 (2 from prior agent + 1 continuation with 2 fixes)
- **Files modified:** 13

## Accomplishments
- Built all 4 dashboard page views consuming API hooks and shared components from Plan 01
- This Week's Picks page renders pick cards with predicted winner, win probability, confidence tier badge, and result indicators
- Season Accuracy page renders 3 summary cards comparing model record against both baselines with Beating/Behind badges, plus week-by-week breakdown table
- Experiments page renders sortable table with expandable detail rows showing params, features, SHAP bars, and hypothesis
- History page renders filterable prediction table with correct/incorrect indicators and URL-synced season/team dropdowns
- Fixed empty state handling on AccuracyPage to show friendly message instead of broken 0/0 N/A display
- Created seed_predictions.py script that generated 256 predictions for the 2023 validation season (62.9% accuracy)

## Task Commits

Each task was committed atomically:

1. **Task 1: Build This Week's Picks and Season Accuracy pages** - `0e5a092` (feat) -- prior agent
2. **Task 2: Build Experiments Scoreboard and Prediction History pages** - `9794d54` (feat) -- prior agent
3. **Task 3: Verify and fix dashboard pages** (continuation):
   - `c4339d6` (fix) -- Add empty state handling to AccuracyPage
   - `9de818e` (feat) -- Add seed_predictions script for development data

## Files Created/Modified
- `frontend/src/components/picks/PickCard.tsx` - Individual game prediction card with confidence tier border, win probability, and result indicator
- `frontend/src/components/picks/PicksGrid.tsx` - Responsive CSS Grid container for pick cards (1-3 columns)
- `frontend/src/pages/ThisWeekPage.tsx` - Landing page with pick cards grid, offseason state, loading/error handling
- `frontend/src/components/accuracy/SummaryCards.tsx` - 3 summary cards: model record, vs always-home, vs better-record with Beating/Behind badges
- `frontend/src/pages/AccuracyPage.tsx` - Season accuracy with summary cards, week-by-week breakdown table, and empty state handling
- `frontend/src/components/experiments/ExperimentTable.tsx` - Sortable table with Collapsible expandable rows, Kept/Reverted badges
- `frontend/src/components/experiments/ExperimentDetail.tsx` - Expanded row: params grid, features list, SHAP top 5 bars, full hypothesis
- `frontend/src/pages/ExperimentsPage.tsx` - Experiment scoreboard with sorting, empty state
- `frontend/src/components/history/HistoryTable.tsx` - History table with ResultIndicator, ConfidenceBadge, formatted dates
- `frontend/src/components/history/HistoryFilters.tsx` - Season and team Select dropdowns
- `frontend/src/pages/HistoryPage.tsx` - Prediction history with URL-synced filters, summary stats, empty state
- `scripts/__init__.py` - Package init for scripts module
- `scripts/seed_predictions.py` - Seed script generating predictions for completed season games

## Decisions Made
- Added empty state handling to AccuracyPage: when API returns empty predictions (e.g., no predictions for current season), show "No Predictions Yet" message instead of rendering SummaryCards with 0/0 N/A
- Created seed_predictions.py as a development utility separate from the production predict pipeline, since it targets completed games (with known outcomes) rather than unplayed games
- The predictions table was missing from the database (DDL in init.sql but not yet applied); created it at runtime before seeding

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] AccuracyPage showed broken display when no predictions exist**
- **Found during:** Task 3 (visual verification checkpoint)
- **Issue:** AccuracyPage rendered SummaryCards with 0/0 N/A and empty week breakdown when API returned empty predictions, appearing broken to users
- **Fix:** Added empty state check after data loads, showing ErrorState with "No Predictions Yet" message
- **Files modified:** frontend/src/pages/AccuracyPage.tsx
- **Verification:** Build passes, page shows empty state message when no predictions
- **Committed in:** c4339d6

**2. [Rule 2 - Missing Critical] No development data available for dashboard**
- **Found during:** Task 3 (visual verification checkpoint)
- **Issue:** Dashboard pages had no prediction data to display because predict_week.py targets unplayed games only. All 2023 games are completed, so the production prediction pipeline cannot generate data for them.
- **Fix:** Created scripts/seed_predictions.py that loads the best model, builds features for 2023, runs inference on all 256 completed games, and stores predictions with actual outcomes
- **Files modified:** scripts/__init__.py, scripts/seed_predictions.py
- **Verification:** Script runs successfully, populates 256 predictions with 62.9% accuracy
- **Committed in:** 9de818e

**3. [Rule 3 - Blocking] predictions table missing from database**
- **Found during:** Task 3 (running seed script)
- **Issue:** The predictions table DDL exists in sql/init.sql but had not been applied to the running database, causing NoSuchTableError
- **Fix:** Created the table via SQLAlchemy text() SQL execution before running the seed script
- **Files modified:** None (runtime database change only)
- **Verification:** Seed script completes successfully after table creation

---

**Total deviations:** 3 auto-fixed (1 bug, 1 missing critical, 1 blocking)
**Impact on plan:** All fixes necessary for dashboard to be usable during development. No scope creep.

## Issues Encountered
- The API's prediction history endpoint defaults to the latest season (2024) which has no seeded predictions. Seeded data is for 2023. Users must navigate to `/history?season=2023` or use the season filter to see data. This is by-design behavior (the API serves the current season), not a bug.

## User Setup Required
To populate the dashboard with development data, run:
```
python -m scripts.seed_predictions
```
This generates 256 predictions for the 2023 validation season.

## Next Phase Readiness
- All 4 dashboard pages are complete and functional
- Phase 5 (Dashboard) is fully complete -- all DASH requirements satisfied
- Phase 6 (Pipeline and Deployment) can proceed with Docker Compose setup
- The seed script provides a pattern for generating predictions during automated pipelines

## Self-Check: PASSED

- All 13 key files verified present on disk
- All 4 task commits (0e5a092, 9794d54, c4339d6, 9de818e) verified in git log
- Build verification: `npm run build` exits 0

---
*Phase: 05-dashboard*
*Completed: 2026-03-17*
