# Phase 9: Dashboard Integration - Research

**Researched:** 2026-03-23
**Domain:** React frontend integration -- adding spread model data to existing dashboard components
**Confidence:** HIGH

## Summary

Phase 9 is a pure frontend integration phase. The backend API (Phase 8) already serves spread predictions via `GET /api/predictions/spreads/week/{season}/{week}` and includes spread model metadata in `GET /api/model/info`. The frontend needs to: (1) add TypeScript types mirroring backend Pydantic schemas, (2) add API fetch functions and TanStack Query hooks for spread data, (3) modify PickCard to display spread predictions and post-game error, (4) add a SpreadSummaryCards section to the Accuracy page, and (5) wire up data fetching on ThisWeekPage and AccuracyPage.

The existing codebase follows a clean, consistent pattern: Pydantic schemas -> TypeScript interfaces -> `apiFetch<T>()` functions -> `useQuery` hooks -> page-level data fetching -> component props. Every piece of this pattern is already established. The phase extends it rather than introducing anything new.

**Primary recommendation:** Follow the existing pattern exactly. Two parallel useQuery calls on ThisWeekPage (classifier + spread), client-side join by game_id, spread data passed as an optional lookup map to PickCard. Agreement breakdown computed client-side from both prediction histories. No new backend endpoints required.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Predicted spread appears **below the confidence percentage**, in smaller muted text
- Format: signed number with label -- e.g., "+7.5 spread" or "-3.2 spread" (home team perspective)
- Positive = home team favored, negative = away team favored
- When spread model is not loaded or no spread data exists for a game, **hide the spread row entirely** -- card looks exactly like v1.0
- Classifier confidence stays the primary visual element (large text); spread is supplementary
- After games complete, **show both the prediction and the result** (card grows slightly taller)
- Pre-game: "+7.5 spread" line only
- Post-game: "+7.5 spread" line PLUS "Actual +10 (off by 2.5)" line below it
- Spread prediction error is **color-coded**: green for close (off by <=3), amber for moderate (3-7), red for far off (>7)
- Existing checkmark/X result indicator stays based on **classifier prediction only**
- One result icon per card, no dual indicators
- **Separate spread section below** existing classifier SummaryCards on the Accuracy page
- Existing 3 classifier cards remain untouched
- New "Spread Model" section with 3 cards: Spread MAE, Spread Winner Accuracy, Agreement/Disagreement Breakdown
- When no spread data exists, **hide the entire spread section** -- Accuracy page looks exactly like v1.0

### Claude's Discretion
- Data fetching strategy: whether to make two API calls (classifier + spread) and merge client-side, or create a combined endpoint
- TypeScript type definitions for spread prediction data
- Exact Tailwind styling, spacing, and typography for new spread elements
- How the agreement/disagreement breakdown is computed (client-side from both prediction sets, or via a new API endpoint)
- Loading skeleton design for spread sections
- Whether to add spread data to the History page as well (if straightforward)

### Deferred Ideas (OUT OF SCOPE)
- Spread-specific history endpoint (deferred from Phase 8) -- evaluate during planning if needed for the agreement breakdown
- Combined classifier+spread predictions endpoint (deferred from Phase 8) -- evaluate during planning

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DASH-01 | Existing PickCards display predicted spread alongside classifier win probability per game | SpreadLabel component receives spread data from PickCard; PicksGrid passes spread lookup map keyed by game_id; data fetched via useSpreadPredictions hook |
| DASH-02 | Dashboard shows spread model MAE on a performance summary | SpreadSummaryCards reads MAE from `useModelInfo().data.spread_model.mae` -- already in ModelInfoResponse from Phase 8 |
| DASH-03 | After games complete, PickCards show actual result and spread prediction error | SpreadLabel component checks `actualSpread` presence, computes error, applies color-coded thresholds (green/amber/red) |
| DASH-04 | Dashboard shows how often spread model picks the correct winner vs the classifier | Agreement breakdown computed client-side by joining classifier history (`usePredictionHistory`) and spread history predictions on game_id, comparing `correct` fields |

</phase_requirements>

## Standard Stack

### Core (Already Installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | ^19.2.4 | UI framework | Already in project |
| TanStack React Query | ^5.90.21 | Data fetching / caching | Already in project, all hooks use this |
| Tailwind CSS | ^4.2.1 | Styling | Already in project |
| shadcn/ui | ^4.0.8 | Component library (Card, Badge, Skeleton, Table) | Already in project |
| TypeScript | ~5.9.3 | Type safety | Already in project |
| lucide-react | ^0.577.0 | Icons | Already in project (used by ResultIndicator) |

### Supporting (Already Installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| class-variance-authority | ^0.7.1 | Variant-based component styling | Used by shadcn Badge component |
| clsx + tailwind-merge | ^2.1.1 / ^3.5.0 | Conditional class merging | `cn()` utility in `lib/utils.ts` |

### No New Dependencies

Phase 9 requires **zero new npm packages**. Everything needed is already installed. The work is purely additive TypeScript/React code using established patterns.

## Architecture Patterns

### Recommended File Structure (New/Modified Files)

```
frontend/src/
├── lib/
│   ├── types.ts              # MODIFY: add SpreadPredictionResponse, SpreadWeekResponse, SpreadModelInfo, update ModelInfoResponse
│   └── api.ts                # MODIFY: add fetchSpreadPredictions(), fetchSpreadHistory()
├── hooks/
│   ├── useSpreadPredictions.ts  # NEW: TanStack Query hook for spread week data
│   └── useSpreadHistory.ts      # NEW: TanStack Query hook for spread history (for agreement breakdown)
├── components/
│   ├── picks/
│   │   ├── SpreadLabel.tsx    # NEW: Renders spread prediction + post-game error on PickCard
│   │   ├── PickCard.tsx       # MODIFY: accept optional spread data, render SpreadLabel
│   │   └── PicksGrid.tsx      # MODIFY: accept spread lookup map, pass to PickCard
│   └── accuracy/
│       └── SpreadSummaryCards.tsx  # NEW: 3-card spread metrics row
├── pages/
│   ├── ThisWeekPage.tsx       # MODIFY: add useSpreadPredictions, build lookup map, pass to PicksGrid
│   └── AccuracyPage.tsx       # MODIFY: add spread section with SpreadSummaryCards
└── (history/HistoryTable.tsx) # OPTIONAL MODIFY: add spread column
```

### Pattern 1: Two Parallel Queries on ThisWeekPage

**What:** ThisWeekPage makes two independent `useQuery` calls -- one for classifier predictions (existing) and one for spread predictions (new). Page renders as soon as classifier data arrives. Spread data joins client-side.

**When to use:** Whenever a page needs data from two independent API endpoints.

**Why this over a combined endpoint:** The spread API endpoint already exists (`GET /api/predictions/spreads/week/{season}/{week}`). Creating a combined endpoint would duplicate backend logic and violate the Phase 8 deferred-ideas boundary. Two parallel queries are the standard TanStack Query pattern and allow independent caching, error handling, and loading states.

**Example:**
```typescript
// ThisWeekPage.tsx
const classifierQuery = useCurrentPredictions();
const spreadQuery = useSpreadPredictions(
  classifierQuery.data?.season,
  classifierQuery.data?.week
);

// Build lookup map for PickCard
const spreadByGameId = useMemo(() => {
  if (!spreadQuery.data?.predictions) return {};
  const map: Record<string, SpreadPredictionResponse> = {};
  for (const sp of spreadQuery.data.predictions) {
    map[sp.game_id] = sp;
  }
  return map;
}, [spreadQuery.data]);
```

**Key detail:** `useSpreadPredictions` must be enabled only when classifier data has loaded (season/week are available), since the spread endpoint requires `{season}/{week}` path params. Use TanStack Query's `enabled` option.

### Pattern 2: Spread Data as Optional Lookup Map

**What:** PicksGrid receives an optional `spreadByGameId: Record<string, SpreadPredictionResponse>` map. PickCard receives an optional `spread?: SpreadPredictionResponse` prop. SpreadLabel renders conditionally based on whether spread data exists.

**When to use:** When adding supplementary data to an existing component without changing its primary data flow.

**Example:**
```typescript
// PicksGrid.tsx
interface PicksGridProps {
  predictions: PredictionResponse[];
  spreadByGameId?: Record<string, SpreadPredictionResponse>;
}

// PickCard.tsx
interface PickCardProps {
  prediction: PredictionResponse;
  spread?: SpreadPredictionResponse;
}
```

**Why optional props:** Ensures backward compatibility. If spread data is unavailable (loading, error, no spread model), the card renders exactly as v1.0. No special error handling needed at the component level.

### Pattern 3: Client-Side Agreement Computation

**What:** The Accuracy page fetches both classifier history (`usePredictionHistory`) and spread prediction history, then computes agreement counts client-side by joining on `game_id`.

**When to use:** When the computation is simple (just counting matches) and both datasets are already loaded.

**Data source for spread history:** The spread API currently only has a per-week endpoint (`GET /api/predictions/spreads/week/{season}/{week}`). For the agreement breakdown, we need ALL completed spread predictions for the season. Two options:

1. **Fetch all weeks individually** -- Requires knowing which weeks have data. Complex, many API calls.
2. **Add a simple spread history fetch** -- The backend `spread_predictions` table contains all the data. A lightweight query function in `api.ts` could hit the existing per-week endpoint iteratively, but this is inefficient.

**Recommended approach:** Add a minimal spread history API function that fetches spread predictions for all completed games. This could either:
- (a) Use the existing spread per-week endpoint with the season's completed weeks (from classifier history data), or
- (b) Add a simple `GET /api/predictions/spreads/history?season={season}` endpoint to the backend

**Decision:** Option (a) is complex. Option (b) is simple but was deferred from Phase 8. Since the agreement breakdown (DASH-04) requires cross-referencing ALL completed games, and the per-week endpoint would need 18+ calls, the most pragmatic approach is to **compute agreement data from the model info response and classifier history** if possible, OR add a minimal spread history endpoint.

**Practical resolution:** The `useModelInfo` response already contains `spread_model.derived_win_accuracy`. For the full agreement breakdown, we DO need per-game spread `correct` values. The simplest path: fetch spread predictions for each completed week found in classifier history. Since classifier history is already loaded, we know which weeks exist. Use a single `useQueries` call to batch these. Alternatively, add one backend endpoint. The planner should evaluate which approach fits the task budget.

### Pattern 4: Conditional Section Rendering

**What:** The entire "Spread Model" section on the Accuracy page renders conditionally based on `modelInfo.spread_model !== null`. If spread model is not loaded, the section is completely absent.

**Example:**
```typescript
{modelQuery.data?.spread_model && (
  <div className="mt-8">
    <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">
      Spread Model
    </h2>
    <SpreadSummaryCards
      spreadModel={modelQuery.data.spread_model}
      classifierAccuracy={historyQuery.data.summary.accuracy}
      agreementData={agreementData}
    />
  </div>
)}
```

### Anti-Patterns to Avoid

- **Modifying SummaryCards.tsx to add spread data:** The user explicitly said existing classifier cards remain untouched. Spread gets its own component.
- **Adding a separate result indicator for spread on PickCard:** One result icon per card (classifier-only). Spread accuracy is shown via the error number.
- **Creating a spread-specific loading state on PickCards:** Per UI-SPEC, PickCards render without spread lines while spread data loads. No skeleton on individual cards.
- **Prop drilling spread data through many layers:** Keep it to PicksGrid -> PickCard -> SpreadLabel. Three levels max.
- **Mixing spread error color logic into SpreadLabel rendering logic:** Extract a pure function like `getSpreadErrorColor(error: number): string` for testability and clarity.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data fetching + caching | Custom fetch state management | TanStack Query `useQuery` | Already established in all hooks, handles loading/error/caching |
| Conditional classes | String concatenation | `cn()` from `lib/utils.ts` | Already used in ConfidenceBadge, project standard |
| Card layout | Custom div styling | shadcn `Card` + `CardContent` | Already used by SummaryCards and PickCard |
| Badge for comparison | Custom styled span | shadcn `Badge` with `ComparisonBadge` pattern | Already implemented in SummaryCards.tsx |
| Number formatting (+sign) | Inline template logic | Extracted `formatSpread(value: number): string` utility | Reused in SpreadLabel pre-game, post-game actual, and potentially History table |

## Common Pitfalls

### Pitfall 1: Spread Query Firing Before Season/Week Available
**What goes wrong:** `useSpreadPredictions(undefined, undefined)` fires immediately on ThisWeekPage, causing a 404 or malformed URL.
**Why it happens:** Classifier query hasn't loaded yet, so season/week are undefined.
**How to avoid:** Use TanStack Query's `enabled` option: `enabled: season != null && week != null`.
**Warning signs:** Console 404 errors on page load, spread data never appearing.

### Pitfall 2: Stale Spread Data After Navigation
**What goes wrong:** Navigating between pages shows stale spread data from a different week.
**Why it happens:** Query key doesn't include season/week, so TanStack Query serves cached data from wrong week.
**How to avoid:** Include season and week in the query key: `["predictions", "spreads", { season, week }]`.
**Warning signs:** Spread data showing wrong week's values after navigation.

### Pitfall 3: Sign Convention Mismatch
**What goes wrong:** Spread shows negative when home team is favored, confusing users.
**Why it happens:** Backend convention (Phase 8): positive = home favored. If frontend negates or reverses, signs flip.
**How to avoid:** Display `predicted_spread` as-is from backend. Format with explicit sign: `+` for >= 0, `-` for negative (inherent in number).
**Warning signs:** "+7.5 spread" showing for away team favored games.

### Pitfall 4: Agreement Breakdown Counting Non-Completed Games
**What goes wrong:** Agreement counts include pending games (where `correct` is null), inflating "Both wrong" or producing NaN.
**Why it happens:** Not filtering out games where either classifier or spread `correct` field is null.
**How to avoid:** Only count games where BOTH predictions have `correct !== null`.
**Warning signs:** Agreement counts not adding up to the total completed games.

### Pitfall 5: TypeScript ModelInfoResponse Breaking Existing Code
**What goes wrong:** Adding `spread_model` to `ModelInfoResponse` type causes existing destructuring or access patterns to fail.
**Why it happens:** The new field is `SpreadModelInfo | null`. If code assumes all fields are non-null, TypeScript complains.
**How to avoid:** The field is optional (null when spread model not loaded). Existing code doesn't touch it. Only new code accesses `modelInfo.spread_model?.mae` etc.
**Warning signs:** TypeScript errors in AccuracyPage or other files that use ModelInfoResponse.

### Pitfall 6: Layout Shift When Spread Data Loads Late
**What goes wrong:** PickCards jump/shift when spread line appears after classifier data renders.
**Why it happens:** SpreadLabel adds height to the card after initial render.
**How to avoid:** Per UI-SPEC, this is acceptable -- the spread line is small (one line of text-sm). No special mitigation needed. The card "grows slightly taller" which is intentional per CONTEXT.md.
**Warning signs:** Visually jarring layout shift. If it's noticeable, consider adding `min-height` to CardContent, but the UI-SPEC explicitly says this is acceptable.

## Code Examples

### TypeScript Types (Mirroring Backend Schemas)

```typescript
// lib/types.ts -- new types to add

export interface SpreadPredictionResponse {
  game_id: string;
  season: number;
  week: number;
  game_date: string | null;
  home_team: string;
  away_team: string;
  predicted_spread: number;
  predicted_winner: string;
  actual_spread: number | null;
  actual_winner: string | null;
  correct: boolean | null;
}

export interface SpreadWeekResponse {
  season: number;
  week: number;
  status: string;
  predictions: SpreadPredictionResponse[];
}

export interface SpreadModelInfo {
  mae: number;
  rmse: number;
  derived_win_accuracy: number;
  training_date: string;
  experiment_id: number;
}

// Update existing ModelInfoResponse:
export interface ModelInfoResponse {
  experiment_id: number;
  training_date: string;
  val_accuracy_2023: number;
  feature_count: number;
  hypothesis: string;
  baseline_always_home: number;
  baseline_better_record: number;
  spread_model: SpreadModelInfo | null;  // NEW
}
```

Source: Backend `api/schemas.py` -- SpreadPredictionResponse, SpreadWeekResponse, SpreadModelInfo, ModelInfoResponse Pydantic models.

### API Fetch Function

```typescript
// lib/api.ts -- new function
export const fetchSpreadPredictions = (
  season: number,
  week: number,
): Promise<SpreadWeekResponse> =>
  apiFetch<SpreadWeekResponse>(
    `/api/predictions/spreads/week/${season}/${week}`,
  );
```

Source: Backend `api/routes/spreads.py` -- `GET /api/predictions/spreads/week/{season}/{week}`.

### TanStack Query Hook with Conditional Enabling

```typescript
// hooks/useSpreadPredictions.ts
import { useQuery } from "@tanstack/react-query";
import { fetchSpreadPredictions } from "@/lib/api";
import type { SpreadWeekResponse } from "@/lib/types";

export function useSpreadPredictions(season?: number, week?: number) {
  return useQuery<SpreadWeekResponse>({
    queryKey: ["predictions", "spreads", { season, week }],
    queryFn: () => fetchSpreadPredictions(season!, week!),
    enabled: season != null && week != null,
  });
}
```

Source: Matches existing hook pattern from `useCurrentPredictions.ts` and `usePredictionHistory.ts`. TanStack Query v5 `enabled` option documented at https://tanstack.com/query/latest/docs/framework/react/guides/dependent-queries.

### Spread Formatting Utility

```typescript
// Helper function (can live in SpreadLabel.tsx or a shared utils file)
function formatSpread(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}`;
}

function getSpreadErrorColor(error: number): string {
  if (error <= 3) return "text-green-400";
  if (error <= 7) return "text-amber-400";
  return "text-red-400";
}
```

Source: CONTEXT.md thresholds (green <=3, amber 3-7, red >7). Sign convention from Phase 8 (positive = home favored).

### SpreadLabel Component Pattern

```typescript
// components/picks/SpreadLabel.tsx
interface SpreadLabelProps {
  predictedSpread?: number;
  actualSpread?: number;
}

export function SpreadLabel({ predictedSpread, actualSpread }: SpreadLabelProps) {
  if (predictedSpread == null) return null;

  const error = actualSpread != null
    ? Math.abs(predictedSpread - actualSpread)
    : null;

  return (
    <div className="flex flex-col gap-0.5">
      <p className="text-sm text-muted-foreground">
        {formatSpread(predictedSpread)} spread
      </p>
      {actualSpread != null && error != null && (
        <p className="text-xs text-muted-foreground">
          Actual {formatSpread(actualSpread)}{" "}
          <span className={`font-semibold ${getSpreadErrorColor(error)}`}>
            (off by {error.toFixed(1)})
          </span>
        </p>
      )}
    </div>
  );
}
```

Source: UI-SPEC interaction contract, CONTEXT.md spread display decisions.

### Agreement Breakdown Computation

```typescript
// Client-side computation for DASH-04
interface AgreementData {
  bothCorrect: number;
  bothWrong: number;
  onlyClassifier: number;
  onlySpread: number;
}

function computeAgreement(
  classifierPredictions: PredictionResponse[],
  spreadPredictions: SpreadPredictionResponse[],
): AgreementData {
  const spreadByGame = new Map(
    spreadPredictions.map((sp) => [sp.game_id, sp])
  );

  const result: AgreementData = {
    bothCorrect: 0,
    bothWrong: 0,
    onlyClassifier: 0,
    onlySpread: 0,
  };

  for (const cp of classifierPredictions) {
    if (cp.correct == null) continue;
    const sp = spreadByGame.get(cp.game_id);
    if (!sp || sp.correct == null) continue;

    if (cp.correct && sp.correct) result.bothCorrect++;
    else if (!cp.correct && !sp.correct) result.bothWrong++;
    else if (cp.correct && !sp.correct) result.onlyClassifier++;
    else result.onlySpread++;
  }

  return result;
}
```

Source: CONTEXT.md agreement card specification, DASH-04 requirement.

## Data Fetching Strategy Analysis

### Option A: Two Parallel API Calls (Recommended)

**ThisWeekPage:**
- `useCurrentPredictions()` -- existing, returns classifier predictions with season/week
- `useSpreadPredictions(season, week)` -- new, enabled after classifier loads

**AccuracyPage:**
- `usePredictionHistory()` -- existing, returns completed classifier predictions
- `useModelInfo()` -- existing, now includes `spread_model` with MAE and derived_win_accuracy
- For agreement breakdown: need spread predictions for ALL completed games

**Pros:** No backend changes. Reuses existing endpoints. Independent caching/error states.
**Cons:** Agreement breakdown requires spread data for all completed games.

### Agreement Breakdown Data Source

The critical question is how to get all spread predictions for the agreement breakdown (DASH-04). Options:

**A1. Fetch spread predictions per-week using `useQueries`:**
- Use classifier history to identify which weeks have completed games
- Fire N parallel spread queries (one per week, typically 18-22 weeks)
- Merge results client-side
- Pros: No backend changes
- Cons: 18+ API calls, complex query orchestration

**A2. Add minimal `GET /api/predictions/spreads/history` backend endpoint:**
- Mirrors existing `GET /api/predictions/history` but for spread_predictions table
- Returns all completed spread predictions for a season
- Pros: Single API call, clean pattern matching classifier history
- Cons: Small backend change (5-minute addition, mirrors existing code)

**A3. Compute from ModelInfoResponse only (partial):**
- `spread_model.derived_win_accuracy` gives the spread winner accuracy number
- But does NOT give per-game breakdown needed for agreement counts
- Pros: Zero new fetches
- Cons: Cannot compute agreement breakdown (DASH-04 incomplete)

**Recommendation:** Option A2 is the most pragmatic. The spread history endpoint is a ~15-line addition to `api/routes/spreads.py` mirroring the existing `predictions.py` history pattern. This was deferred from Phase 8 but is necessary for DASH-04. The planner should include this as a small task.

If the planner prefers to avoid backend changes entirely, Option A1 works but is more complex and requires careful `useQueries` orchestration.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| React Query v3/v4 `useQueries` API | TanStack Query v5 `useQueries` with object syntax | v5 (2023) | Same concept, updated API signature |
| Separate loading states per query | TanStack Query `combine` results pattern | v5 | Can combine multiple query results into one |
| `react-router-dom` v6 | `react-router` v7 | 2024 | Package rename, same API for this use case |

**No deprecated patterns in use.** The codebase is already on current versions of all dependencies.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None detected in frontend |
| Config file | None -- frontend has no test setup |
| Quick run command | N/A |
| Full suite command | `cd frontend && npm run build` (TypeScript type checking via `tsc -b`) |

The frontend project has no test framework (no vitest, jest, or testing-library). The only automated validation is `tsc -b && vite build` which catches TypeScript errors and build failures.

### Phase Requirements --> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | PickCards display predicted spread | manual | Visual inspection: load ThisWeekPage with spread data in DB | N/A |
| DASH-02 | Dashboard shows spread MAE | manual | Visual inspection: load AccuracyPage, verify MAE card shows | N/A |
| DASH-03 | Post-game cards show actual + error | manual | Visual inspection: load ThisWeekPage/HistoryPage with completed games | N/A |
| DASH-04 | Dashboard shows spread vs classifier winner comparison | manual | Visual inspection: load AccuracyPage, verify agreement breakdown card | N/A |

### Sampling Rate

- **Per task commit:** `cd frontend && npm run build` (type-checks + bundles)
- **Per wave merge:** `cd frontend && npm run build && npm run lint`
- **Phase gate:** Build succeeds + manual visual verification against UI-SPEC

### Wave 0 Gaps

- No test framework in frontend -- all validation is manual visual inspection + TypeScript build
- This is consistent with the existing project (Phases 1-8 have no frontend tests)
- Backend has tests (pytest) but frontend does not -- this is the project's established pattern

## Open Questions

1. **Spread History Endpoint for Agreement Breakdown**
   - What we know: DASH-04 requires per-game spread `correct` values to compute agreement counts. The backend only has a per-week spread endpoint.
   - What's unclear: Whether to add a backend spread history endpoint (simple, ~15 lines) or orchestrate multiple per-week fetches client-side.
   - Recommendation: Add `GET /api/predictions/spreads/history?season={season}` to backend. Mirrors existing classifier history pattern. The planner should make the call.

2. **History Page Spread Column**
   - What we know: UI-SPEC says "at Claude's discretion during planning -- this is lower priority."
   - What's unclear: Whether to include in the plan or defer.
   - Recommendation: Include as a low-priority optional task in the last plan. HistoryTable already has a clean table structure; adding a "Spread" column is mechanical.

## Sources

### Primary (HIGH confidence)
- `api/schemas.py` -- Backend Pydantic schemas defining SpreadPredictionResponse, SpreadWeekResponse, SpreadModelInfo, ModelInfoResponse
- `api/routes/spreads.py` -- Spread week endpoint implementation
- `api/routes/model.py` -- Model info endpoint including spread_model nested object
- `frontend/src/lib/types.ts` -- Existing TypeScript interfaces (need updating)
- `frontend/src/lib/api.ts` -- Existing API fetch functions (need extending)
- `frontend/src/hooks/*.ts` -- Existing TanStack Query hook patterns
- `frontend/src/components/picks/PickCard.tsx` -- Current PickCard structure to modify
- `frontend/src/components/accuracy/SummaryCards.tsx` -- Current SummaryCards pattern to replicate
- `frontend/src/pages/AccuracyPage.tsx` -- Current Accuracy page structure
- `frontend/src/pages/ThisWeekPage.tsx` -- Current This Week page structure
- `.planning/phases/09-dashboard-integration/09-CONTEXT.md` -- User decisions
- `.planning/phases/09-dashboard-integration/09-UI-SPEC.md` -- Visual/interaction contract
- `frontend/package.json` -- Dependency versions confirmed

### Secondary (MEDIUM confidence)
- TanStack Query v5 `enabled` option for dependent queries -- standard documented pattern
- TanStack Query v5 `useQueries` for parallel batch queries -- standard documented pattern

### Tertiary (LOW confidence)
- None -- all findings based on direct codebase inspection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies, all libraries already in use and verified in package.json
- Architecture: HIGH -- all patterns directly observed in existing codebase, extending established conventions
- Pitfalls: HIGH -- identified from direct code analysis (query enabling, sign conventions, type safety)
- Data fetching strategy: MEDIUM -- the agreement breakdown data source requires a planner decision (backend endpoint vs multi-fetch)

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable -- no moving parts, all dependencies locked)
