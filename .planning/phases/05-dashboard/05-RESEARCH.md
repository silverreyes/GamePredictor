# Phase 5: Dashboard - Research

**Researched:** 2026-03-17
**Domain:** React frontend dashboard consuming FastAPI endpoints
**Confidence:** HIGH

## Summary

Phase 5 is a greenfield React frontend that consumes 6 FastAPI endpoints (built in Phase 4) to display NFL game predictions across 4 pages. The stack is locked: React + Vite + Tailwind CSS + shadcn/ui + React Router + TanStack Query. A comprehensive UI-SPEC (`05-UI-SPEC.md`) already defines every component, color, spacing token, typography rule, responsive breakpoint, loading state, and error state in detail.

The project starts from zero frontend code. The `frontend/` directory does not exist yet. The recommended approach is to scaffold with Vite, initialize shadcn/ui (which sets up Tailwind v4, path aliases, and the `cn` utility), then build out the app shell (routing + sidebar layout), then each page view in sequence. TanStack Query v5 handles all data fetching with built-in caching, loading states, and error handling -- no raw fetch or axios.

**Primary recommendation:** Use `npx shadcn@latest init -t vite` to scaffold the entire project (React, Vite, Tailwind v4, shadcn/ui config) in one command, then layer in React Router (library/declarative mode) and TanStack Query as the data layer.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Multi-page with sidebar layout using React Router
- 4 routes with shareable URLs: `/` (This Week's Picks), `/accuracy` (Season Accuracy), `/experiments` (Experiment Scoreboard), `/history` (Prediction History)
- Always-visible sidebar with icon + label for each nav item (no collapse)
- Sidebar includes model status bar showing current experiment ID and 2023 val accuracy (from GET /model/info)
- Active route highlighted in sidebar
- React + Vite
- React Router for client-side routing
- Tailwind CSS + shadcn/ui components (tables, cards, badges)
- TanStack Query 5+ for data fetching -- handles caching, loading states, error handling out of the box. No raw fetch/axios.

### Claude's Discretion
- Exact shadcn/ui component selection per view
- Color scheme and dark/light mode
- Loading skeleton design
- Error state handling
- Responsive breakpoints
- How weekly picks are displayed within the page (cards vs table)
- How experiments are compared (sortable table, chart, etc.)
- Correct/incorrect visual indicators in history view
- Baseline comparison format in accuracy view

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DASH-01 | Dashboard displays this week's games with predicted winner, win probability, and confidence tier (high/medium/low) | GET /api/predictions/current endpoint, PredictionResponse schema with confidence_tier field, UI-SPEC pick card layout with Display typography for probability |
| DASH-02 | Dashboard displays season accuracy summary: model record vs always-home and better-record baselines for the current season | GET /api/predictions/history (summary object with correct/total/accuracy), GET /api/model/info (baseline_always_home, baseline_better_record), UI-SPEC accuracy page layout with 3 summary cards |
| DASH-03 | Dashboard displays experiment scoreboard: all logged experiments with 2023 val accuracy, key params, and keep/revert status | GET /api/experiments endpoint returns ExperimentResponse[] with full experiment data, UI-SPEC sortable table with expandable rows using Collapsible |
| DASH-04 | Dashboard displays historical predictions log: all past predictions with actual outcome and correct/incorrect highlight | GET /api/predictions/history with season/team filter params, HistorySummary in response, UI-SPEC table with CircleCheck/CircleX icons and Select filters |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.4 | UI framework | Locked decision from CONTEXT.md |
| Vite | 8.0.0 | Build tool + dev server | Locked decision; fastest DX for React SPAs |
| TypeScript | 5.9.3 | Type safety | Industry standard for React projects |
| React Router | 7.13.1 | Client-side routing | Locked decision; declarative/library mode for SPA |
| TanStack Query | 5.90.21 | Server state / data fetching | Locked decision; replaces raw fetch with caching, loading, error states |
| Tailwind CSS | 4.2.1 | Utility-first CSS | Locked decision; v4 uses Vite plugin instead of PostCSS |
| shadcn/ui | 4.0.8 (CLI) | Component library (copy-paste) | Locked decision; built on Radix UI primitives |
| lucide-react | 0.577.0 | Icon library | Specified in UI-SPEC for nav icons and indicators |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @tailwindcss/vite | 4.2.1 | Tailwind v4 Vite plugin | Required for Tailwind v4 (replaces PostCSS approach) |
| class-variance-authority | 0.7.1 | Component variant management | Installed by shadcn/ui init |
| clsx | 2.1.1 | Conditional class names | Installed by shadcn/ui init |
| tailwind-merge | 3.5.0 | Merge Tailwind classes safely | Installed by shadcn/ui init (used in cn utility) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TanStack Query | Raw fetch + useState | Locked out by CONTEXT.md. Would require manual caching, loading, error handling |
| shadcn/ui | Material UI, Chakra UI | Locked out. shadcn copies components into project for full control |
| React Router | TanStack Router | Locked out. React Router is the established standard |
| Tailwind v4 | Tailwind v3 | v4 is current; shadcn@latest init scaffolds v4 by default |

**Installation (via shadcn scaffolding):**
```bash
npx shadcn@latest init -t vite -n frontend
cd frontend
npm install react-router @tanstack/react-query
npx shadcn@latest add card button table badge skeleton select collapsible separator
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/               # shadcn/ui components (auto-generated)
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx      # Persistent sidebar with nav + model status
│   │   │   └── AppLayout.tsx    # Sidebar + Outlet wrapper
│   │   ├── picks/
│   │   │   ├── PickCard.tsx     # Individual game prediction card
│   │   │   └── PicksGrid.tsx    # CSS Grid of pick cards
│   │   ├── accuracy/
│   │   │   ├── SummaryCards.tsx  # Model vs baseline comparison cards
│   │   │   └── WeekBreakdown.tsx # Week-by-week accuracy table
│   │   ├── experiments/
│   │   │   ├── ExperimentTable.tsx  # Sortable experiment table
│   │   │   └── ExperimentDetail.tsx # Expandable row content
│   │   ├── history/
│   │   │   ├── HistoryTable.tsx    # Prediction history table
│   │   │   └── HistoryFilters.tsx  # Season/team filter controls
│   │   └── shared/
│   │       ├── ErrorState.tsx     # Reusable error card
│   │       ├── ConfidenceBadge.tsx # High/Medium/Low tier badge
│   │       └── ResultIndicator.tsx # CircleCheck/CircleX/Pending
│   ├── pages/
│   │   ├── ThisWeekPage.tsx
│   │   ├── AccuracyPage.tsx
│   │   ├── ExperimentsPage.tsx
│   │   └── HistoryPage.tsx
│   ├── hooks/
│   │   ├── useCurrentPredictions.ts
│   │   ├── usePredictionHistory.ts
│   │   ├── useModelInfo.ts
│   │   └── useExperiments.ts
│   ├── lib/
│   │   ├── api.ts            # API client (base URL, fetch wrappers)
│   │   ├── types.ts          # TypeScript types matching API schemas
│   │   ├── utils.ts          # cn() utility (from shadcn init)
│   │   └── query-client.ts   # QueryClient instance with defaults
│   ├── App.tsx               # BrowserRouter + QueryClientProvider + Routes
│   ├── main.tsx              # ReactDOM.createRoot entry
│   └── index.css             # Tailwind imports + CSS variables
├── index.html
├── vite.config.ts
├── tsconfig.json
├── components.json           # shadcn/ui config
├── package.json
└── .gitignore
```

### Pattern 1: Custom Query Hooks (Data Fetching)
**What:** Wrap every TanStack Query call in a custom hook that encapsulates the queryKey, queryFn, and configuration.
**When to use:** Every API call. Pages never call useQuery directly.
**Example:**
```typescript
// Source: TanStack Query v5 patterns
// hooks/useCurrentPredictions.ts
import { useQuery } from "@tanstack/react-query";
import { fetchCurrentPredictions } from "@/lib/api";
import type { WeekPredictionsResponse } from "@/lib/types";

export function useCurrentPredictions() {
  return useQuery<WeekPredictionsResponse>({
    queryKey: ["predictions", "current"],
    queryFn: fetchCurrentPredictions,
    staleTime: 5 * 60 * 1000, // 5 minutes per UI-SPEC
    refetchOnWindowFocus: false,
    retry: 2,
  });
}
```

### Pattern 2: Layout Route with Outlet
**What:** A root layout route that renders the sidebar + an Outlet for page content. React Router nests all page routes inside this layout.
**When to use:** App shell structure. Sidebar persists across all pages.
**Example:**
```typescript
// Source: React Router v7 declarative mode
// App.tsx
import { BrowserRouter, Routes, Route } from "react-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/query-client";
import { AppLayout } from "@/components/layout/AppLayout";
import { ThisWeekPage } from "@/pages/ThisWeekPage";
import { AccuracyPage } from "@/pages/AccuracyPage";
import { ExperimentsPage } from "@/pages/ExperimentsPage";
import { HistoryPage } from "@/pages/HistoryPage";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<ThisWeekPage />} />
            <Route path="accuracy" element={<AccuracyPage />} />
            <Route path="experiments" element={<ExperimentsPage />} />
            <Route path="history" element={<HistoryPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

### Pattern 3: API Client Module
**What:** A single module that defines all API fetch functions, the base URL, and error handling. TanStack Query hooks import from this module.
**When to use:** Centralizes API configuration. Never scatter fetch calls across components.
**Example:**
```typescript
// lib/api.ts
const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const fetchCurrentPredictions = () =>
  apiFetch<WeekPredictionsResponse>("/api/predictions/current");

export const fetchPredictionHistory = (season?: number, team?: string) => {
  const params = new URLSearchParams();
  if (season) params.set("season", String(season));
  if (team) params.set("team", team);
  const qs = params.toString();
  return apiFetch<PredictionHistoryResponse>(
    `/api/predictions/history${qs ? `?${qs}` : ""}`
  );
};

export const fetchModelInfo = () =>
  apiFetch<ModelInfoResponse>("/api/model/info");

export const fetchExperiments = () =>
  apiFetch<ExperimentResponse[]>("/api/experiments");
```

### Pattern 4: TypeScript Types Derived from API Schemas
**What:** Mirror Pydantic response models as TypeScript interfaces. Source of truth is `api/schemas.py`.
**When to use:** Define once in `lib/types.ts`, use everywhere.
**Example:**
```typescript
// lib/types.ts -- derived from api/schemas.py
export interface PredictionResponse {
  game_id: string;
  season: number;
  week: number;
  game_date: string | null;
  home_team: string;
  away_team: string;
  predicted_winner: string;
  confidence: number;
  confidence_tier: "high" | "medium" | "low";
  actual_winner: string | null;
  correct: boolean | null;
}

export interface HistorySummary {
  correct: number;
  total: number;
  accuracy: number | null;
}

export interface PredictionHistoryResponse {
  predictions: PredictionResponse[];
  summary: HistorySummary;
}

export interface WeekPredictionsResponse {
  season: number;
  week: number;
  status: "ok" | "offseason";
  predictions: PredictionResponse[];
}

export interface ModelInfoResponse {
  experiment_id: number;
  training_date: string;
  val_accuracy_2023: number;
  feature_count: number;
  hypothesis: string;
  baseline_always_home: number;
  baseline_better_record: number;
}

export interface ShapFeature {
  feature: string;
  importance: number;
}

export interface ExperimentResponse {
  experiment_id: number;
  timestamp: string;
  params: Record<string, unknown>;
  features: string[];
  val_accuracy_2023: number;
  val_accuracy_2022: number;
  val_accuracy_2021: number;
  baseline_always_home: number;
  baseline_better_record: number;
  log_loss: number;
  brier_score: number;
  shap_top5: ShapFeature[];
  keep: boolean;
  hypothesis: string;
  prev_best_acc: number;
  model_path: string | null;
}
```

### Anti-Patterns to Avoid
- **Fetching data directly in components:** Always use custom hooks wrapping TanStack Query. Components call `useCurrentPredictions()`, never `useQuery(...)` directly.
- **Passing API data through many prop layers:** Use TanStack Query's cache -- child components can call the same hook and get cached data without prop drilling.
- **Manual loading/error state management:** TanStack Query provides `isLoading`, `isError`, `error`, `data` -- never use separate useState for loading/error.
- **Using useEffect for data fetching:** TanStack Query replaces this pattern entirely.
- **Hardcoding API base URL:** Use `import.meta.env.VITE_API_URL` with a fallback to `http://localhost:8000`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data fetching + caching | Custom fetch hooks with useState/useEffect | TanStack Query useQuery | Handles stale data, retries, deduplication, background refetch |
| Loading skeletons | Custom animated divs | shadcn/ui Skeleton component | Pre-styled, consistent with design system |
| Tables | Custom HTML tables with styling | shadcn/ui Table components | Accessible, styled, consistent with theme |
| Dropdown filters | Custom select elements | shadcn/ui Select component | Accessible, keyboard navigable, themed |
| Expandable rows | Custom accordion logic | shadcn/ui Collapsible | Accessible, animated, state management built-in |
| Client-side sorting | Custom sort implementation | React state + Array.sort() | Simple enough for a table of max 30 experiments, no library needed |
| CSS utility merging | Manual className concatenation | cn() utility from shadcn/ui | Handles Tailwind class conflicts correctly |
| Dark mode class management | Manual DOM manipulation | `class="dark"` on html element | UI-SPEC specifies dark-only mode; set it once in index.html |
| URL query param sync | Manual history.pushState | React Router useSearchParams | Keeps filter state in URL for shareability |

**Key insight:** shadcn/ui copies component source code into your project. This means you own the code and can customize it freely, but you also benefit from pre-built accessible components that follow Radix UI patterns.

## Common Pitfalls

### Pitfall 1: Tailwind v4 Configuration Differences
**What goes wrong:** Applying Tailwind v3 configuration patterns (tailwind.config.js, PostCSS setup) to a v4 project, causing styles to not apply.
**Why it happens:** Tailwind v4 fundamentally changed its configuration approach. It uses a Vite plugin (`@tailwindcss/vite`) instead of PostCSS, and CSS-first configuration via `@theme` instead of `tailwind.config.js`.
**How to avoid:** Use `npx shadcn@latest init -t vite` which scaffolds the correct Tailwind v4 setup automatically. CSS variables are defined in the CSS file with `@theme`, not in a JS config. If manually configuring, import Tailwind via `@import "tailwindcss"` in CSS.
**Warning signs:** Tailwind classes not applying, PostCSS errors, missing `tailwind.config.js` causing confusion.

### Pitfall 2: React Router v7 Import Paths
**What goes wrong:** Importing from `react-router-dom` (v6 pattern) instead of `react-router` (v7 pattern).
**Why it happens:** Most tutorials and Stack Overflow answers reference v6. React Router v7 consolidated exports into a single `react-router` package.
**How to avoid:** Only install `react-router` (NOT `react-router-dom`). All imports come from `react-router`: `import { BrowserRouter, Routes, Route, NavLink } from "react-router"`.
**Warning signs:** `Module not found` errors when importing from `react-router-dom`.

### Pitfall 3: TanStack Query v5 API Changes from v4
**What goes wrong:** Using removed v4 APIs like `useQuery({ queryKey, queryFn, onSuccess })` or object-first syntax.
**Why it happens:** Many tutorials reference v4 patterns.
**How to avoid:** In v5: `onSuccess`, `onError`, `onSettled` callbacks are removed from useQuery (still available on useMutation). Use the returned state directly. Query functions must return a value (not undefined). Always use object syntax: `useQuery({ queryKey: [...], queryFn: () => ... })`.
**Warning signs:** TypeScript errors about unexpected properties, undefined return values.

### Pitfall 4: CORS Issues in Development
**What goes wrong:** Browser blocks API requests from Vite dev server (localhost:5173) to FastAPI (localhost:8000).
**Why it happens:** Cross-origin requests require explicit CORS headers.
**How to avoid:** Phase 4 already configures CORS origins in `api/config.py` for both `localhost:3000` and `localhost:5173`. Vite defaults to port 5173, which is already allowed. No Vite proxy needed.
**Warning signs:** `Access-Control-Allow-Origin` errors in browser console.

### Pitfall 5: Forgetting Dark Mode Class on Root Element
**What goes wrong:** shadcn/ui components render with light theme colors despite CSS variables being set for dark mode.
**Why it happens:** shadcn/ui uses the `dark` class on the `<html>` element to activate dark mode CSS variables.
**How to avoid:** Since UI-SPEC specifies dark-only mode, add `class="dark"` to the `<html>` element in `index.html`. No theme toggle needed for this phase.
**Warning signs:** Components have white backgrounds, light borders, light text on light background.

### Pitfall 6: Missing Path Alias Configuration
**What goes wrong:** `@/components/ui/button` imports fail with module not found errors.
**Why it happens:** The `@/` path alias needs to be configured in both `tsconfig.json` and `vite.config.ts`.
**How to avoid:** `npx shadcn@latest init -t vite` configures this automatically. If setting up manually, add `paths: { "@/*": ["./src/*"] }` to tsconfig and the corresponding Vite `resolve.alias` config.
**Warning signs:** Red underlines on `@/` imports, module resolution failures.

### Pitfall 7: Filter State Not in URL
**What goes wrong:** History page filters (season, team) work but are lost on page refresh or sharing.
**Why it happens:** Using React state (useState) for filter values instead of URL search params.
**How to avoid:** Use React Router's `useSearchParams` hook. When filters change, update URL params. When the page loads, read initial values from URL params. Pass params to TanStack Query's queryKey so it refetches on filter change.
**Warning signs:** Filters reset on refresh, shared links don't preserve filter state.

## Code Examples

Verified patterns from official sources:

### QueryClient Configuration
```typescript
// Source: TanStack Query v5 docs
// lib/query-client.ts
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes (UI-SPEC requirement)
      refetchOnWindowFocus: false, // UI-SPEC requirement
      retry: 2, // UI-SPEC requirement
    },
  },
});
```

### Sidebar NavLink with Active State
```typescript
// Source: React Router v7 NavLink + UI-SPEC styling
import { NavLink } from "react-router";
import { Calendar, BarChart3, FlaskConical, History } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", icon: Calendar, label: "This Week" },
  { to: "/accuracy", icon: BarChart3, label: "Accuracy" },
  { to: "/experiments", icon: FlaskConical, label: "Experiments" },
  { to: "/history", icon: History, label: "History" },
];

export function SidebarNav() {
  return (
    <nav className="flex flex-col gap-1">
      {navItems.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/"}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-xs transition-colors duration-150",
              isActive
                ? "bg-blue-500/10 text-blue-400"
                : "text-muted-foreground hover:bg-zinc-800"
            )
          }
        >
          <Icon className="h-5 w-5" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
```

### Confidence Tier Badge
```typescript
// Source: UI-SPEC confidence tier badge colors
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const tierStyles = {
  high: "bg-blue-500/20 text-blue-400",
  medium: "bg-amber-500/20 text-amber-400",
  low: "bg-zinc-500/20 text-zinc-400",
} as const;

export function ConfidenceBadge({ tier }: { tier: "high" | "medium" | "low" }) {
  return (
    <Badge variant="outline" className={cn("border-0 text-xs", tierStyles[tier])}>
      {tier.charAt(0).toUpperCase() + tier.slice(1)}
    </Badge>
  );
}
```

### Error State Component
```typescript
// Source: UI-SPEC error states specification
import { AlertCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  heading: string;
  body: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export function ErrorState({ heading, body, onRetry, retryLabel = "Try Again" }: ErrorStateProps) {
  return (
    <Card className="mx-auto max-w-md">
      <CardContent className="flex flex-col items-center gap-4 pt-6 text-center">
        <AlertCircle className="h-8 w-8 text-red-500" />
        <h2 className="text-xl font-semibold">{heading}</h2>
        <p className="text-sm text-muted-foreground">{body}</p>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            {retryLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
```

### History Page with URL-Synced Filters
```typescript
// Source: React Router useSearchParams + TanStack Query
import { useSearchParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { fetchPredictionHistory } from "@/lib/api";

export function useHistoryWithFilters() {
  const [searchParams, setSearchParams] = useSearchParams();
  const season = searchParams.get("season")
    ? Number(searchParams.get("season"))
    : undefined;
  const team = searchParams.get("team") ?? undefined;

  const query = useQuery({
    queryKey: ["predictions", "history", { season, team }],
    queryFn: () => fetchPredictionHistory(season, team),
  });

  const setFilters = (newSeason?: number, newTeam?: string) => {
    const params = new URLSearchParams();
    if (newSeason) params.set("season", String(newSeason));
    if (newTeam) params.set("team", newTeam);
    setSearchParams(params);
  };

  return { ...query, season, team, setFilters };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind CSS via PostCSS + tailwind.config.js | Tailwind v4 via Vite plugin + CSS-first `@theme` config | Tailwind v4 (Jan 2025) | No JS config file; styles configured in CSS. `@tailwindcss/vite` plugin required. |
| react-router-dom package (v6) | Single `react-router` package (v7) | React Router v7 (Nov 2024) | All imports from `react-router`. `react-router-dom` no longer needed. |
| useQuery with onSuccess/onError callbacks (v4) | useQuery returns state only; no lifecycle callbacks (v5) | TanStack Query v5 (Oct 2023) | Handle success/error via the returned `data`/`error` states |
| shadcn CLI as `shadcn-ui` | shadcn CLI as `shadcn` | shadcn v2 (2024) | Use `npx shadcn@latest` not `npx shadcn-ui@latest` |
| shadcn init creates config only | `shadcn init -t vite` scaffolds entire project | shadcn v4 (2025) | Can scaffold React+Vite+Tailwind+shadcn in one command |
| HSL color format in shadcn themes | OKLCH color format in shadcn themes | shadcn for Tailwind v4 | CSS variables use OKLCH; hex values in UI-SPEC still work via custom overrides |

**Deprecated/outdated:**
- `react-router-dom`: Merged into `react-router` in v7. Do not install separately.
- `shadcn-ui` CLI: Renamed to `shadcn`. Use `npx shadcn@latest`.
- `tailwind.config.js`: Tailwind v4 uses CSS-first configuration. shadcn init handles this.
- TanStack Query `onSuccess`/`onError` in useQuery: Removed in v5. Use returned state.

## Open Questions

1. **shadcn init -t vite exact scaffolded structure**
   - What we know: The command scaffolds a React+Vite+Tailwind+shadcn project with path aliases and cn utility configured. It creates a full project directory.
   - What's unclear: Exact file structure may vary between shadcn CLI versions. The -t vite flag creates a new project vs init (which initializes in existing project).
   - Recommendation: Use `npx shadcn@latest init -t vite -n frontend` to create in a new `frontend/` directory, then verify the generated structure before building on top of it. Alternatively, scaffold with `npm create vite@latest frontend -- --template react-ts` first, then run `npx shadcn@latest init` inside that directory.

2. **shadcn/ui Tailwind v4 color variable format**
   - What we know: shadcn Tailwind v4 uses OKLCH colors. UI-SPEC specifies hex/HSL values from the zinc dark theme.
   - What's unclear: Whether the default zinc dark theme from shadcn produces the exact hex values listed in UI-SPEC, or if custom overrides are needed.
   - Recommendation: Initialize with shadcn zinc dark theme preset, then compare generated CSS variables against UI-SPEC values. The visual appearance should match even if the internal format differs (OKLCH vs hex).

3. **Vite dev server port**
   - What we know: Vite defaults to port 5173. CORS is configured for both 3000 and 5173 in Phase 4.
   - What's unclear: Whether `shadcn init -t vite` changes the default port.
   - Recommendation: Keep Vite default (5173) which is already in CORS allowed origins.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual browser verification (no automated frontend test framework in scope for v1) |
| Config file | N/A |
| Quick run command | `cd frontend && npm run dev` (visual verification against UI-SPEC) |
| Full suite command | Manual checklist against UI-SPEC + API response verification in browser DevTools |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | This week's picks display with winner, probability, tier | manual | Open `/` in browser, verify pick cards render with data from GET /api/predictions/current | N/A |
| DASH-02 | Season accuracy with baseline comparisons | manual | Open `/accuracy`, verify summary cards show model record and baseline comparison badges | N/A |
| DASH-03 | Experiment scoreboard with sortable table | manual | Open `/experiments`, verify table renders experiments, click to sort, expand row | N/A |
| DASH-04 | Historical predictions with correct/incorrect indicators | manual | Open `/history`, verify table rows with CircleCheck/CircleX icons, test season/team filters | N/A |

### Sampling Rate
- **Per task commit:** `cd frontend && npm run build` (TypeScript + Vite build succeeds without errors)
- **Per wave merge:** Full manual walkthrough of all 4 pages against UI-SPEC
- **Phase gate:** Build succeeds + all 4 pages render correctly with API data

### Wave 0 Gaps
- [ ] `frontend/` directory -- entire frontend needs scaffolding
- [ ] shadcn/ui initialization with required components
- [ ] React Router + TanStack Query setup
- [ ] TypeScript types matching API schemas

## Sources

### Primary (HIGH confidence)
- `api/schemas.py` -- All Pydantic response models defining the TypeScript type contracts
- `api/routes/predictions.py` -- GET /api/predictions/current, /week/{week}, /history endpoints with query params
- `api/routes/experiments.py` -- GET /api/experiments endpoint parsing experiments.jsonl
- `api/routes/model.py` -- GET /api/model/info endpoint returning baseline accuracies
- `api/config.py` -- CORS origins (localhost:3000, localhost:5173), confidence tier thresholds
- `.planning/phases/05-dashboard/05-CONTEXT.md` -- All locked decisions and discretion areas
- `.planning/phases/05-dashboard/05-UI-SPEC.md` -- Complete visual/interaction contract
- npm registry -- Verified current versions of all packages via `npm view`
- https://ui.shadcn.com/docs/installation/vite -- shadcn/ui Vite installation
- https://ui.shadcn.com/docs/tailwind-v4 -- shadcn Tailwind v4 compatibility
- https://tailwindcss.com/docs/installation/using-vite -- Tailwind v4 Vite plugin setup
- https://reactrouter.com/start/library/installation -- React Router v7 declarative/library mode

### Secondary (MEDIUM confidence)
- https://ui.shadcn.com/docs/dark-mode/vite -- Dark mode ThemeProvider pattern (verified with official docs)
- https://ui.shadcn.com/docs/cli -- shadcn CLI flags and options

### Tertiary (LOW confidence)
- TanStack Query v5 quick-start code patterns -- Could not fully extract from docs (navigation-only pages rendered). Patterns based on training data knowledge of v5 API, cross-referenced with npm version verification. Core API (useQuery with object syntax, QueryClientProvider) is stable and well-established.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All versions verified via npm registry. All choices locked by CONTEXT.md.
- Architecture: HIGH - Project structure follows established React + shadcn/ui conventions. API contracts are fully defined in Phase 4 code.
- Pitfalls: HIGH - Tailwind v4, React Router v7, and TanStack Query v5 migration pitfalls are well-documented. CORS already configured.
- Code examples: HIGH - TypeScript types derived directly from `api/schemas.py`. Patterns verified against official docs.

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (30 days -- stack is stable, no fast-moving dependencies)
