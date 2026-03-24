# Architecture Patterns

**Domain:** Design system migration, landing page, and experiments redesign for existing NFL prediction dashboard
**Researched:** 2026-03-24
**Confidence:** HIGH -- recommendations are based on direct codebase inspection of all 40+ source files, official Tailwind v4/shadcn/ui documentation, and React Router v7 patterns.

## Existing Architecture Snapshot

Before describing integration patterns, here is the current system as of v1.1:

```
                    nostradamus.silverreyes.net
                              |
                          [Caddy] (HTTPS termination)
                              |
                          [Nginx] (:8080 -> :80)
                         /         \
                        /           \
              [Static SPA]     [FastAPI :8000]
            React + Vite          /api/*
          Tailwind v4 + shadcn    |
          4 pages, Sidebar nav   PostgreSQL
                                  |
                              experiments.jsonl (file-based)
```

**Frontend stack:** React 19 + React Router 7 (SPA mode, BrowserRouter) + TanStack Query + Tailwind v4 + shadcn/ui (base-nova style, neutral base) + Vite 7.

**Routing:** Single `<AppLayout>` wrapper with `<Sidebar>` + `<Outlet>`. Four routes: `/` (This Week), `/accuracy`, `/experiments`, `/history`. The index route (`/`) renders `ThisWeekPage`.

**Theming:** Dark-only (class="dark" on `<html>`). CSS variables in `:root` and `.dark` using oklch. Font imports via Google Fonts (Inter + JetBrains Mono). The `@theme inline` block maps CSS vars to Tailwind color utilities.

**Component library:** 11 shadcn/ui primitives (badge, button, card, collapsible, select, separator, skeleton, table, tooltip) plus 12 custom domain components across `accuracy/`, `experiments/`, `history/`, `picks/`, `shared/`, `layout/`.

---

## 1. Routing Restructure: Home Page as Default

### Current State

```typescript
// App.tsx -- current
<Route element={<AppLayout />}>
  <Route index element={<ThisWeekPage />} />
  <Route path="accuracy" element={<AccuracyPage />} />
  <Route path="experiments" element={<ExperimentsPage />} />
  <Route path="history" element={<HistoryPage />} />
</Route>
```

The index route (`/`) renders `ThisWeekPage` directly. During offseason, this shows an "Offseason" error state with a link to History -- a poor landing experience.

### Recommended Pattern: Two Layouts, Home as Index

The Home/landing page has a fundamentally different layout than the dashboard pages. The landing page should be full-width, no sidebar. The dashboard pages keep the existing sidebar layout.

```typescript
// App.tsx -- recommended
<Routes>
  {/* Landing page -- full-width, no sidebar */}
  <Route index element={<HomePage />} />

  {/* Dashboard pages -- sidebar layout */}
  <Route element={<AppLayout />}>
    <Route path="this-week" element={<ThisWeekPage />} />
    <Route path="accuracy" element={<AccuracyPage />} />
    <Route path="experiments" element={<ExperimentsPage />} />
    <Route path="history" element={<HistoryPage />} />
  </Route>

  {/* Catch-all redirect to home */}
  <Route path="*" element={<Navigate to="/" replace />} />
</Routes>
```

### Why This Pattern

1. **Home gets its own layout.** The landing page needs full viewport width, no sidebar chrome. Nesting it inside `AppLayout` would fight the sidebar margin (`md:ml-[180px]`).

2. **This Week moves to `/this-week`.** Currently at `/`, which will now be Home. The path change is acceptable because there are no external links to the old `/` URL that expected This Week content (it is a subdomain with no SEO history for specific paths).

3. **No off-season routing logic needed.** The Home page is always appropriate. Users navigate from Home to specific dashboard sections via CTAs. The "Offseason" state in `ThisWeekPage` remains as-is for users who navigate there directly.

4. **Sidebar updates.** Add a Home icon/link at the top of the nav. Update `navItems` array:

```typescript
const navItems = [
  { to: "/", icon: Home, label: "Home" },
  { to: "/this-week", icon: Calendar, label: "This Week" },
  { to: "/accuracy", icon: BarChart3, label: "Accuracy" },
  { to: "/experiments", icon: FlaskConical, label: "Experiments" },
  { to: "/history", icon: History, label: "History" },
] as const;
```

### Component Impact

| Component | Change | Reason |
|-----------|--------|--------|
| `App.tsx` | **Modified** -- new route structure | Add Home route, move This Week to `/this-week` |
| `Sidebar.tsx` | **Modified** -- new nav item, brand link | Add Home to navItems, link "Nostradamus" title to `/` |
| `AppLayout.tsx` | **No change** | Still wraps dashboard pages via `<Outlet>` |
| `HomePage.tsx` | **New** | Landing page component, full-width |
| `ThisWeekPage.tsx` | **No change** | Same component, just mounted at `/this-week` |

### Nginx Consideration

The SPA fallback (`try_files $uri $uri/ /index.html`) already handles all client-side routes. No nginx configuration changes needed for new routes.

---

## 2. Design System Migration: Theme Override Strategy

### Current Theme Architecture

```
index.css
  |
  +-- @import "tailwindcss"
  +-- @import Google Fonts (Inter, JetBrains Mono)
  +-- @import "tw-animate-css"
  +-- @import "shadcn/tailwind.css"
  +-- @custom-variant dark
  |
  +-- :root { ... 30+ CSS variables in oklch ... }
  +-- .dark { ... 30+ CSS variables in oklch ... }
  |
  +-- @theme inline { ... maps vars to --color-* and --font-* ... }
  |
  +-- @layer base { ... body/html defaults ... }
```

All theming lives in a single file: `src/index.css`. The shadcn/ui components reference these variables through Tailwind utilities (`bg-card`, `text-muted-foreground`, etc.), which are mapped via the `@theme inline` block.

### silverreyes.net Design System Tokens

The portfolio site uses CSS custom properties with a different naming convention:

| silverreyes.net Token | Purpose | Nostradamus Equivalent |
|----------------------|---------|----------------------|
| `--color-text` | Primary text | `--foreground` |
| `--color-text-muted` | Secondary text | `--muted-foreground` |
| `--color-text-faint` | Tertiary text | (no equivalent, add) |
| `--color-accent` | Interactive highlight | `--primary` or new `--accent` |
| `--color-border` | Dividers | `--border` |
| `--color-surface` | Card backgrounds | `--card` |
| `--color-surface-2` | Elevated surfaces | (no equivalent, add) |
| `--font-display` | Headings | (no equivalent, add) |
| `--font-mono` | Labels, metadata | `--font-mono` (exists) |
| `--font-body` | Body copy | `--font-sans` (exists) |
| `--space-xs/sm/md/lg` | Spacing scale | (use Tailwind spacing) |
| `--text-micro/label/body/heading/lg` | Type scale | (use Tailwind text scale) |

### Recommended Migration Strategy: Override In-Place

Do NOT create a separate theme file or import chain. Override the existing CSS variables in `index.css` directly, preserving the shadcn/ui variable names so all existing components continue working.

```css
/* index.css -- MODIFIED, not replaced */

@import "tailwindcss";
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap');
@import "tw-animate-css";
@import "shadcn/tailwind.css";
@custom-variant dark (&:is(.dark *));

/* ===== silverreyes.net design alignment ===== */

.dark {
  /* Surfaces -- aligned with silverreyes.net dark palette */
  --background: oklch(0.13 0.005 260);    /* was: oklch(0.145 0 0) */
  --card: oklch(0.17 0.005 260);           /* was: oklch(0.205 0 0) */
  --popover: oklch(0.17 0.005 260);
  --sidebar: oklch(0.15 0.005 260);

  /* Text hierarchy -- matches silverreyes text/text-muted/text-faint */
  --foreground: oklch(0.95 0.01 260);      /* --color-text */
  --muted-foreground: oklch(0.65 0.01 260); /* --color-text-muted */

  /* Accent -- the interactive highlight from silverreyes */
  --primary: oklch(0.75 0.15 250);          /* accent color, adjust to match */
  --primary-foreground: oklch(0.15 0.005 260);

  /* Border */
  --border: oklch(1 0 0 / 8%);

  /* ... remaining variables ... */
}
```

### Why Override In-Place

1. **Zero component breakage.** Every existing component uses `bg-card`, `text-muted-foreground`, etc. These resolve to the same CSS variable names. Changing the values changes the look without touching any component code.

2. **shadcn/ui compatibility preserved.** Future `npx shadcn@latest add [component]` commands will generate components that reference the standard variable names and work immediately.

3. **Single source of truth.** One file to audit, one file to update. No cascade conflicts between a "base theme" and an "override theme."

### New Variables to Add

The silverreyes.net design system has a few concepts that shadcn/ui does not. Add these as new variables and map them in `@theme inline`:

```css
:root {
  /* Extended tokens from silverreyes.net */
  --text-faint: oklch(0.45 0 0);
  --surface-elevated: oklch(0.97 0 0);
}

.dark {
  --text-faint: oklch(0.45 0.01 260);
  --surface-elevated: oklch(0.22 0.005 260);
}

@theme inline {
  /* ... existing mappings ... */
  --color-text-faint: var(--text-faint);
  --color-surface-elevated: var(--surface-elevated);
}
```

This makes `text-text-faint` and `bg-surface-elevated` available as Tailwind utilities without disrupting existing ones.

### Font Strategy

The current site imports Inter (body) and JetBrains Mono (code). silverreyes.net uses a display font for headings. Two options:

**Option A (recommended): Add a display font, keep Inter for body.**
```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap');
```

Map in `@theme inline`:
```css
@theme inline {
  --font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;
  --font-display: 'Space Grotesk', 'Inter', ui-sans-serif, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;
}
```

Then use `font-display` on headings in the landing page and section headers. Existing body text continues using `font-sans` (Inter) unchanged.

**Note:** The actual display font choice depends on what silverreyes.net uses. The above is a placeholder. The implementation phase should inspect the actual font-face declarations on the live site to match exactly.

### Where New CSS Variables and Font Imports Live

**Everything stays in `src/index.css`.** This is the single entry point for:
- Tailwind base import
- Font imports (Google Fonts URL)
- shadcn/ui import
- All CSS custom properties (`:root` and `.dark`)
- The `@theme inline` mapping block
- Base layer styles

Do not split into multiple CSS files. The Tailwind v4 + shadcn/ui architecture is designed around a single CSS entry point, and Vite bundles it efficiently regardless.

---

## 3. Experiments Page Redesign: Table to Card/Detail View

### Current Data Flow

```
experiments.jsonl (file on disk)
       |
  FastAPI /api/experiments (reads file, returns JSON array)
       |
  useExperiments() hook (TanStack Query, queryKey: ["experiments"])
       |
  ExperimentsPage (loading/error/empty states)
       |
  ExperimentTable (sortable table with collapsible rows)
       |
  ExperimentDetail (expanded row: hypothesis, params, features, SHAP bars)
```

The `ExperimentResponse` type carries: `experiment_id`, `timestamp`, `params` (dict), `features` (string[]), `val_accuracy_2023/2022/2021`, baselines, `log_loss`, `brier_score`, `shap_top5`, `keep`, `hypothesis`, `prev_best_acc`, `model_path`.

### Current UX Problems

1. **Truncated hypothesis.** The table truncates hypothesis text to 60 chars. The hypothesis is the most important context for each experiment.
2. **Cramped detail view.** `ExperimentDetail` renders inside a collapsed table row, constrained to table cell width.
3. **No visual hierarchy.** All experiments look the same. The "kept" (deployed) experiment is not visually prominent.

### Recommended Pattern: Card Grid + Slide-Out Detail

Replace the table with a card grid. Each card shows the experiment summary. Clicking a card opens a detail panel (either inline expansion or a slide-in panel).

```
ExperimentsPage
  |
  +-- ExperimentFilters (sort by: id, accuracy; filter: kept/reverted)
  |
  +-- ExperimentCardGrid (CSS grid, 1-2 columns)
  |     |
  |     +-- ExperimentCard (one per experiment)
  |           - experiment_id, keep badge, hypothesis (full text)
  |           - val_accuracy_2023 (primary metric, large)
  |           - val_accuracy_2022, 2021, log_loss (secondary metrics row)
  |           - click -> expand or navigate
  |
  +-- ExperimentDetailPanel (expanded view for selected experiment)
        - Full hypothesis
        - Parameters grid
        - Feature list
        - SHAP Top 5 bar chart
        - Comparison vs baselines
        - Timestamp, model path
```

### Component Structure

| Component | Status | Responsibility |
|-----------|--------|----------------|
| `ExperimentsPage.tsx` | **Modified** | Manages selected experiment state, renders grid + detail |
| `ExperimentCardGrid.tsx` | **New** | CSS grid container, receives sorted/filtered experiments |
| `ExperimentCard.tsx` | **New** | Summary card for one experiment |
| `ExperimentDetailPanel.tsx` | **New** (replaces `ExperimentDetail.tsx`) | Full detail view, not constrained to table cell |
| `ExperimentTable.tsx` | **Removed** | Replaced by card grid |
| `ExperimentDetail.tsx` | **Removed** | Replaced by detail panel |
| `ExperimentFilters.tsx` | **New** | Sort/filter controls (optional, could be inline) |

### Data Flow Changes

**None.** The API endpoint, hook, and TypeScript types remain identical. The only change is how `ExperimentResponse[]` is rendered.

```
useExperiments() hook -- NO CHANGE
       |
  ExperimentsPage -- MODIFIED (state management for selected card)
       |
  ExperimentCardGrid + ExperimentDetailPanel -- NEW rendering
```

### Selected Experiment State

Use `useState<number | null>` for the selected experiment ID (same pattern as the current `expandedId`). The detail panel renders conditionally below the grid or as a slide-in overlay.

**Inline expansion (recommended):**
```typescript
function ExperimentsPage() {
  const { data } = useExperiments();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const selected = data?.find(e => e.experiment_id === selectedId);

  return (
    <div>
      <h1>Experiment Scoreboard</h1>
      <ExperimentCardGrid
        experiments={data}
        selectedId={selectedId}
        onSelect={setSelectedId}
      />
      {selected && <ExperimentDetailPanel experiment={selected} />}
    </div>
  );
}
```

**Why inline expansion over a modal/sheet:** The experiments page is a reference view, not a transactional flow. Users want to compare experiments visually. A modal obscures the cards. An inline detail panel below the grid keeps context visible and allows quick switching between experiments.

### Card Layout Specification

```
+--------------------------------------------------+
|  #5                                     [Kept]   |
|                                                   |
|  Lower learning rate with early stopping          |
|  for better convergence on validation set         |
|                                                   |
|  63.7%                                            |
|  2023 validation                                  |
|                                                   |
|  2022: 60.2%  |  2021: 58.4%  |  LogLoss: 0.632  |
+--------------------------------------------------+
```

- Experiment ID top-left, Keep/Revert badge top-right
- Full hypothesis text (no truncation)
- Primary metric (2023 val accuracy) as hero number
- Secondary metrics in a row at bottom
- The "kept" experiment gets a subtle accent border (left border or ring) to visually distinguish it

---

## 4. New Component Inventory

### Landing Page Components

| Component | Path | Purpose |
|-----------|------|---------|
| `HomePage.tsx` | `pages/` | Landing page, orchestrates sections |
| `HeroSection.tsx` | `components/home/` | Hero with title, subtitle, CTA buttons |
| `HowItWorksSection.tsx` | `components/home/` | 3-step explanation (data, model, predict) |
| `ExploreCTAs.tsx` | `components/home/` | Card grid linking to dashboard sections |
| `HomeFooter.tsx` | `components/home/` | Footer with links back to silverreyes.net |

### Experiments Redesign Components

| Component | Path | Status |
|-----------|------|--------|
| `ExperimentCardGrid.tsx` | `components/experiments/` | New |
| `ExperimentCard.tsx` | `components/experiments/` | New |
| `ExperimentDetailPanel.tsx` | `components/experiments/` | New (replaces ExperimentDetail) |
| `ExperimentTable.tsx` | `components/experiments/` | Remove |
| `ExperimentDetail.tsx` | `components/experiments/` | Remove |

### Modified Components

| Component | Change |
|-----------|--------|
| `App.tsx` | Route restructure |
| `Sidebar.tsx` | Add Home nav item, update branding |
| `index.css` | Theme variable overrides, new font, new tokens |
| `ExperimentsPage.tsx` | Card grid instead of table, selected state |

---

## 5. File Structure After v1.2

```
frontend/src/
  App.tsx                          -- MODIFIED (routing)
  index.css                        -- MODIFIED (theme overrides)
  main.tsx                         -- no change

  components/
    layout/
      AppLayout.tsx                -- no change
      Sidebar.tsx                  -- MODIFIED (nav items, branding)

    home/                          -- NEW directory
      HeroSection.tsx
      HowItWorksSection.tsx
      ExploreCTAs.tsx
      HomeFooter.tsx

    experiments/
      ExperimentCardGrid.tsx       -- NEW
      ExperimentCard.tsx           -- NEW
      ExperimentDetailPanel.tsx    -- NEW
      ExperimentTable.tsx          -- REMOVED
      ExperimentDetail.tsx         -- REMOVED

    accuracy/                      -- no change
    history/                       -- no change
    picks/                         -- no change
    shared/                        -- no change
    ui/                            -- no change (shadcn primitives)

  hooks/                           -- no change
  lib/                             -- no change
  pages/
    HomePage.tsx                   -- NEW
    ThisWeekPage.tsx               -- no change (path changes to /this-week)
    AccuracyPage.tsx               -- no change
    ExperimentsPage.tsx            -- MODIFIED (card grid rendering)
    HistoryPage.tsx                -- no change
```

---

## 6. Build Order and Dependencies

The three workstreams have a clear dependency chain:

```
  [1. Theme Override]
         |
         v
  [2. Landing Page]  +  [3. Experiments Redesign]
     (needs theme)       (needs theme)
```

### Phase ordering rationale

**Theme must come first** because both the landing page and the experiments redesign will use the new design tokens (colors, fonts, spacing). Building pages before the theme means either: (a) building with old tokens and reworking later, or (b) hardcoding values that should come from the theme.

**Landing page and experiments redesign are independent** of each other. They can be built in parallel or in either order. The landing page requires the routing restructure, which is a small change (5 lines in `App.tsx`, 3 lines in `Sidebar.tsx`).

### Suggested build sequence

1. **Theme migration** (index.css override, font import, new tokens, verify existing pages look correct)
2. **Route restructure** (move This Week to `/this-week`, add Home route, update Sidebar)
3. **Landing page** (build HomePage with sections using new theme)
4. **Experiments redesign** (replace table with cards, build detail panel)

Steps 3 and 4 could be a single phase or two parallel phases depending on scope preference.

---

## 7. Hardcoded Color Audit

Several existing components use hardcoded Tailwind color classes instead of theme variables. These will need updating during the theme migration to ensure consistency:

| Component | Hardcoded Classes | Should Become |
|-----------|------------------|---------------|
| `Sidebar.tsx` | `bg-zinc-900`, `border-zinc-800`, `hover:bg-zinc-800`, `bg-blue-500/10`, `text-blue-400` | `bg-sidebar`, `border-sidebar-border`, `hover:bg-sidebar-accent`, `bg-primary/10`, `text-primary` |
| `ExperimentTable.tsx` | `hover:bg-zinc-800/50`, `bg-zinc-900/50` | `hover:bg-muted`, `bg-muted/50` |
| `ExperimentDetail.tsx` | `bg-zinc-800`, `bg-blue-500` | `bg-muted`, `bg-primary` |
| `PickCard.tsx` | `border-blue-500`, `border-amber-500`, `border-zinc-500` | Semantic confidence tier colors (keep or map to theme) |
| `SummaryCards.tsx` | `bg-green-500/20`, `text-green-400`, `bg-red-500/20`, `text-red-400` | Semantic success/destructive colors |
| `AccuracyPage.tsx` | `hover:bg-zinc-800/50` | `hover:bg-muted` |

**Note:** The green/red badge colors (`bg-green-500/20`, etc.) and confidence tier borders (`border-blue-500`, etc.) are semantic -- they encode meaning (correct/incorrect, confidence level). These should remain as Tailwind color utilities, not theme variables. Only the structural/chrome colors (backgrounds, borders, hover states) need to migrate to theme tokens.

---

## 8. Anti-Patterns to Avoid

### Anti-Pattern 1: Separate Theme CSS File
**What:** Creating a `theme.css` or `silverreyes-theme.css` that imports alongside or overrides `index.css`.
**Why bad:** CSS specificity fights. The `@theme inline` block in `index.css` already maps variables. A second file either duplicates the mapping or creates ordering-dependent overrides that break on import order changes.
**Instead:** Modify `index.css` directly. One file, one truth.

### Anti-Pattern 2: Wrapping Home in AppLayout
**What:** Adding Home as another route inside the `<Route element={<AppLayout />}>` wrapper.
**Why bad:** AppLayout adds sidebar + margin-left to all children. The landing page needs full viewport width. You would have to conditionally hide the sidebar on Home, which creates layout-shift bugs and complex conditional rendering.
**Instead:** Home gets its own route outside the AppLayout wrapper.

### Anti-Pattern 3: URL-Based Experiment Detail (/experiments/:id)
**What:** Making each experiment a separate route with URL params.
**Why bad:** Over-engineering. There are only 5-10 experiments. The data is already fetched in a single array. Adding routing means managing URL state, back-button behavior, and loading states for individual experiments. The current click-to-expand pattern is simpler and sufficient.
**Instead:** Keep `useState` for selected experiment. The card grid + inline detail panel is a single-page interaction.

### Anti-Pattern 4: Tailwind Config File for Theme
**What:** Creating a `tailwind.config.ts` to define theme extensions.
**Why bad:** Tailwind v4 eliminated the config file in favor of CSS-first configuration. The `@theme inline` block in `index.css` IS the config. Adding a config file creates a v3/v4 hybrid that confuses tooling and IDE completion.
**Instead:** All theme customization goes through CSS variables + `@theme inline` in `index.css`.

### Anti-Pattern 5: Conditional Layout in AppLayout
**What:** Checking `useLocation()` in `AppLayout` to conditionally render sidebar based on current route.
**Why bad:** Violates single-responsibility. AppLayout should always render sidebar + content area. Route-level layout decisions belong in the route tree, not inside a layout component.
**Instead:** Use React Router's nested route structure. Routes outside `<Route element={<AppLayout />}>` do not get the sidebar. This is the intended pattern.

---

## 9. Scalability Considerations

| Concern | Current (v1.1) | After v1.2 | Notes |
|---------|----------------|------------|-------|
| Route count | 4 | 5 | No performance concern |
| CSS bundle size | ~5KB (single theme) | ~6KB (expanded theme) | Negligible |
| Font loading | 2 fonts (Inter, JetBrains Mono) | 3 fonts (+display) | Use `display=swap` to prevent FOIT |
| Component count | ~23 | ~28 (+5 new, -2 removed) | Well within manageable range |
| API endpoints | 7 | 7 (no changes) | Experiments redesign is frontend-only |
| Build time | ~2s (Vite) | ~2s (Vite) | No impact |

---

## Sources

- **shadcn/ui Theming (official):** https://ui.shadcn.com/docs/theming -- CSS variable structure, oklch format, @theme inline pattern [HIGH confidence]
- **shadcn/ui Tailwind v4 Guide (official):** https://ui.shadcn.com/docs/tailwind-v4 -- v4-specific integration, forwardRef removal, color format migration [HIGH confidence]
- **Tailwind CSS v4 Theme Variables (official):** https://tailwindcss.com/docs/theme -- @theme directive, CSS-first configuration [HIGH confidence]
- **React Router v7 Routing (official):** https://reactrouter.com/start/framework/routing -- Nested routes, index routes, layout routes [HIGH confidence]
- **silverreyes.net (live site inspection):** https://silverreyes.net -- Design tokens extracted via web fetch, CSS variable naming convention [MEDIUM confidence -- actual oklch values not extractable, only variable names]
- **Codebase inspection:** All 40+ frontend source files read directly [HIGH confidence]
