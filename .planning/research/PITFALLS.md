# Domain Pitfalls

**Domain:** Design system migration and landing page for existing NFL prediction dashboard (React + Tailwind v4 + shadcn/ui)
**Researched:** 2026-03-24
**Confidence:** HIGH (findings verified against codebase inspection, official Tailwind v4 docs, shadcn/ui docs, and community discussions)

---

## Critical Pitfalls

Mistakes that cause visual regressions across the entire dashboard, break production routing, or require large-scale rework.

---

### Pitfall 1: Hardcoded Tailwind Color Classes Resist Theme Changes

**What goes wrong:** The current codebase uses 48 hardcoded color utility classes (e.g., `bg-zinc-800`, `text-blue-400`, `border-zinc-800`, `bg-green-500/20`) across 16 files. These are direct Tailwind color palette references, not CSS variable-backed semantic tokens. When the design system palette changes from the current zinc/blue scheme to the silverreyes.net palette, every one of these 48 references must be individually found and updated. Missing even one creates an inconsistent visual -- a zinc-800 sidebar border surrounded by the new palette's surface colors.

**Why it happens:** shadcn/ui components themselves use CSS variable-backed classes (`bg-background`, `text-foreground`, `bg-muted`, `text-muted-foreground`), which re-theme cleanly when you change the `:root` variables. But developer-authored code (Sidebar, PickCard, ExperimentTable, ConfidenceBadge, HistoryTable, etc.) bypassed the variable system and used raw Tailwind colors. This is natural during initial development -- `bg-zinc-800` is concrete and readable -- but it creates a shadow theme that the CSS variable system cannot reach.

**Consequences:** Partial theme application. The shadcn/ui primitives (Card, Badge, Table) pick up the new palette through CSS variables, but the layout chrome (sidebar, nav, hover states) and semantic colors (success green, error red, warning amber, confidence blue) remain pinned to the old zinc/blue scheme. The dashboard looks like two different apps merged together.

**Specific locations in this codebase:**
- `Sidebar.tsx`: 8 hardcoded references (bg-zinc-900, border-zinc-800, bg-blue-500/10, text-blue-400, hover:bg-zinc-800)
- `ExperimentTable.tsx`: 4 references (hover:bg-zinc-800/50, bg-zinc-900/50, bg-green-500/20, bg-red-500/20)
- `PickCard.tsx`: 4 references (border-blue-500, border-amber-500, border-zinc-500)
- `ConfidenceBadge.tsx`: 3 references (bg-blue-500/20 text-blue-400, bg-amber-500/20, bg-zinc-500/20)
- `HistoryTable.tsx`, `SpreadLabel.tsx`, `HistoryLegend.tsx`, `ResultIndicator.tsx`, `SummaryCards.tsx`, `SpreadSummaryCards.tsx`, `ErrorState.tsx`: remaining 29 references

**Prevention:**
1. Create a semantic color layer in CSS variables BEFORE changing any palette values. Define variables like `--color-success`, `--color-danger`, `--color-warning`, `--color-accent`, `--color-surface-elevated`, `--color-surface-sunken`, `--color-nav-active`, `--color-nav-active-bg` in `:root` and `.dark`.
2. Expose these through `@theme inline` as `--color-success: var(--success)`, etc., so they become Tailwind utilities (`text-success`, `bg-surface-elevated`).
3. Replace all 48 hardcoded references with the new semantic tokens in a single dedicated pass.
4. THEN swap the underlying color values to the silverreyes.net palette. Because everything references semantic tokens, the swap is a single-file change to `:root` variables.
5. Never skip step 3. Changing the palette first and then chasing hardcoded colors leads to a broken intermediate state that is hard to QA.

**Detection:** After the palette swap, visually inspect every page. Any zinc, blue, green, red, or amber that does not match the new palette is a missed hardcoded reference. A grep for `zinc-|slate-|blue-[0-9]|green-[0-9]|red-[0-9]|amber-[0-9]` in `src/` should return zero hits (outside of the semantic color definition file itself).

**Phase relevance:** Must be the FIRST step of the design system phase. Do the semantic token migration before any palette changes.

---

### Pitfall 2: Landing Page Route Breaks Existing Index Route and Bookmarks

**What goes wrong:** The current `App.tsx` has `<Route index element={<ThisWeekPage />} />` -- the root path `/` renders This Week. The v1.2 plan adds a landing page at `/`. If this is done by replacing the index route, every existing user bookmark to `nostradamus.silverreyes.net/` now shows a marketing landing page instead of their weekly picks. If This Week moves to `/picks` or `/this-week`, existing bookmarks to the root path break silently (they land on the wrong page, not a 404).

**Why it happens:** The root path `/` can only have one handler. React Router's `index` route is unambiguous. Adding a new page to the root requires moving the existing page, which changes the URL contract with users.

**Consequences:** Users who bookmarked the root URL get a landing page instead of picks. The off-season routing logic (mentioned in requirements: "Home instead of empty This Week") adds further complexity -- the root path behavior now depends on whether the NFL season is active. Users during the season want picks at `/`; off-season users should see the landing page. Getting this conditional wrong means the wrong content shows at the wrong time.

**Prevention:**
1. Place the landing page at `/` with a NEW layout (no sidebar). Place This Week at `/picks` with the existing `AppLayout` (sidebar).
2. Use React Router's multiple layout pattern: sibling `<Route>` groups at the top level, one wrapping the landing page in a `LandingLayout`, one wrapping dashboard pages in `AppLayout`.
3. Add a redirect from `/` to `/picks` during the active season if desired, OR make the landing page always be the entry point with a prominent "View This Week's Picks" CTA.
4. For backward compatibility, add a `<Route path="this-week" element={<Navigate to="/picks" replace />} />` catch for any old links, though this codebase has not exposed `/this-week` before.
5. The critical decision: does `/` ALWAYS show the landing page (simpler, predictable) or conditionally route based on season status (complex, requires API call before routing)? Recommendation: always show the landing page at `/`, with a hero CTA that goes to `/picks`. Simpler, no conditional routing bugs.

**Detection:** After the route change, test: direct navigation to `/`, `/picks`, `/accuracy`, `/experiments`, `/history`. Test browser back/forward. Test hard refresh on each route (nginx `try_files` must serve `index.html` for the new `/picks` path -- this already works because the existing nginx config catches all non-file paths).

**Phase relevance:** Route restructuring should happen early, before building the landing page content, so the layout infrastructure is in place.

---

### Pitfall 3: Dual Layout Architecture Breaks Sidebar Margin Assumptions

**What goes wrong:** The current `AppLayout.tsx` applies a fixed left margin to `<main>`: `md:ml-[180px] lg:ml-60`. This compensates for the fixed-position sidebar. The landing page needs a full-width layout WITHOUT this margin. If the landing page is accidentally rendered inside `AppLayout`, it will have a 240px left margin with a sidebar it does not need. If the landing page creates its own layout but shares components (like a footer or navigation), CSS from the two layouts can conflict.

**Why it happens:** The entire app currently assumes a single layout. Every page gets the sidebar. Adding a second layout (full-width, no sidebar) to the same router requires restructuring the route tree.

**Consequences:** Landing page renders with a phantom left margin and a visible sidebar. Or the sidebar disappears from dashboard pages. Or the mobile top nav (which is also in `Sidebar.tsx`) appears on the landing page where it should not.

**Prevention:**
1. Create a `LandingLayout` component that renders `<Outlet />` without any sidebar or margin.
2. Structure routes as two sibling groups:
   ```tsx
   <Routes>
     <Route element={<LandingLayout />}>
       <Route index element={<LandingPage />} />
     </Route>
     <Route element={<AppLayout />}>
       <Route path="picks" element={<ThisWeekPage />} />
       <Route path="accuracy" element={<AccuracyPage />} />
       <Route path="experiments" element={<ExperimentsPage />} />
       <Route path="history" element={<HistoryPage />} />
     </Route>
   </Routes>
   ```
3. The `LandingLayout` should have its OWN navigation (a simple top bar with the brand and a "Dashboard" link), completely separate from the sidebar.
4. Do NOT try to make `AppLayout` conditionally show/hide the sidebar based on the current route. That creates coupling and is fragile.

**Detection:** Render the landing page and inspect the computed margin-left on the main content area. It should be 0, not 180px or 240px.

**Phase relevance:** Must be resolved when setting up the route structure, before building either the landing page or any navigation changes.

---

## Moderate Pitfalls

---

### Pitfall 4: CSS Variable Naming Collision Between Custom Tokens and shadcn/ui

**What goes wrong:** The current `index.css` defines shadcn/ui's standard CSS variables (`--background`, `--foreground`, `--primary`, `--muted`, etc.) in `:root` and then maps them in `@theme inline` as `--color-background: var(--background)`. Adding custom semantic tokens (e.g., `--success`, `--danger`, `--accent`) risks colliding with shadcn/ui's existing `--accent` variable. The shadcn/ui `--accent` means "interactive element background" while a design system `--accent` might mean "brand highlight color." Overwriting `--accent` changes the look of shadcn/ui's Select, Collapsible, and Badge components in unexpected ways.

**Why it happens:** shadcn/ui occupies a large chunk of the semantic color namespace (`primary`, `secondary`, `accent`, `muted`, `destructive`). Custom design system tokens often want similar names.

**Consequences:** Changing `--accent` to the silverreyes.net brand color makes every shadcn/ui component that uses `bg-accent` (dropdown highlights, collapsible triggers, sidebar items) turn the brand color instead of the intended subtle background. The Badge component's `secondary` variant changes unexpectedly.

**Prevention:**
1. Namespace custom tokens with a prefix: `--brand-accent`, `--brand-success`, `--brand-surface` rather than bare `--accent`, `--success`, `--surface`.
2. OR map the silverreyes.net palette TO the existing shadcn/ui variable names, understanding exactly what each variable controls:
   - `--primary` = main action buttons, primary badges
   - `--secondary` = secondary buttons, subtle backgrounds
   - `--accent` = interactive element hover/active states in dropdowns, sidebar, collapsible
   - `--muted` = subdued backgrounds, disabled text
   - `--destructive` = error/danger states
3. Option 2 is cleaner if the silverreyes.net palette can naturally map to these semantics. Option 1 is safer if the palette has more colors than shadcn/ui's variable set can express.
4. Before changing any variable value, list every shadcn/ui component in use (Card, Badge, Table, Skeleton, Select, Collapsible, Separator, Tooltip, Button) and check which variables they reference. The `card.tsx` component uses `bg-card`, `text-card-foreground`, `ring-foreground/10`. The `badge.tsx` uses `bg-primary`, `text-primary-foreground`, `bg-secondary`, `bg-destructive`. Know the blast radius.

**Detection:** After changing CSS variables, render every page and inspect each shadcn/ui component. Pay special attention to hover states, focus rings, and dropdown menus -- these are the hardest to spot because they only appear on interaction.

**Phase relevance:** Design system phase, specifically the CSS variable mapping step.

---

### Pitfall 5: @theme inline Variables Not Overridable in Dark Mode

**What goes wrong:** Variables defined inside `@theme inline` are resolved at build time and do not generate global CSS custom properties that can be overridden. If you define `--color-brand: oklch(0.5 0.2 250)` inside `@theme inline`, you cannot override it in `.dark { --brand: oklch(0.8 0.15 250); }` the same way you can with the shadcn/ui pattern. The existing codebase avoids this problem because it defines raw CSS variables in `:root` and `.dark`, then maps them in `@theme inline`. But if new custom colors are added directly in `@theme inline` without the `:root`/`.dark` pattern, dark mode variants will not work.

**Why it happens:** Tailwind v4's `@theme inline` is designed for values that reference CSS variables, not for defining the variables themselves. The indirection (`@theme inline` -> `var(--some-var)` -> `:root` defines `--some-var`) is what enables dark mode to work. Skipping the indirection breaks the override chain.

**Consequences:** New custom colors work in light mode but are stuck at their light-mode values in dark mode. If the project currently only uses dark mode (the current codebase appears to be dark-only based on the zinc-900 sidebar), this manifests later if light mode is ever added. More immediately, it creates a pattern that future developers will copy, accumulating technical debt.

**Prevention:**
1. Follow the established pattern exactly: define raw variables in BOTH `:root` and `.dark`, then map in `@theme inline`.
2. For every new color token: `--brand-accent: oklch(...)` in `:root`, different value in `.dark`, then `--color-brand-accent: var(--brand-accent)` in `@theme inline`.
3. Never put literal color values directly in `@theme inline`. Always reference a `var()`.

**Detection:** Search `@theme inline` for any literal oklch/hsl/rgb values that are not wrapped in `var()`. These are dark-mode-incompatible.

**Phase relevance:** Design system phase. Enforce this pattern from the first new color token.

---

### Pitfall 6: Font Loading Flash (FOUT) When Switching from Google Fonts CDN to Custom Fonts

**What goes wrong:** The current `index.css` loads Inter and JetBrains Mono from Google Fonts CDN via `@import url('https://fonts.googleapis.com/...')`. This import is render-blocking -- the browser waits for the font before painting text (FOIT in some browsers, FOUT in others). If the silverreyes.net design system uses different fonts and the loading strategy changes (e.g., self-hosting), there is a visible flash of unstyled text on initial load. On slower connections, text appears in the system font for 100-500ms before swapping to the custom font, causing a layout shift as metrics differ.

**Why it happens:** Google Fonts CSS includes `font-display: swap` by default (visible in the `display=swap` URL parameter), which causes FOUT. Self-hosted fonts without explicit `font-display` cause FOIT (invisible text). Either way, the user sees a visual glitch on first load. The problem is worse on subsequent page loads if fonts are not properly cached.

**Consequences:** Cumulative Layout Shift (CLS) penalty when text reflows after font swap. Users see a flash of system font on every cold load. If the new font has significantly different metrics than the fallback, elements jump and resize visibly.

**Prevention:**
1. Self-host fonts as WOFF2 files in the project's `public/fonts/` directory. This eliminates the external DNS lookup and connection to Google's CDN.
2. Use `font-display: swap` in `@font-face` declarations for body text (users see text immediately in fallback, then swap).
3. Use `font-display: optional` for decorative/display fonts used only in the hero (if the font does not load in time, the fallback is used for that page load -- no layout shift).
4. Add `<link rel="preload" as="font" type="font/woff2" href="/fonts/YourFont.woff2" crossorigin>` in `index.html` for the primary body font. This tells the browser to start downloading the font immediately, before CSS is parsed.
5. Define a fallback stack with `size-adjust` to match the custom font's metrics: `font-family: 'CustomFont', 'Inter', ui-sans-serif, system-ui, sans-serif`. The `size-adjust` on the fallback `@font-face` can minimize the text reflow.
6. Subset fonts to include only Latin characters if the dashboard is English-only, reducing file size from ~100KB to ~20KB.

**Detection:** Throttle network to Slow 3G in DevTools and reload. Watch for text appearing in system font before switching. Check CLS score in Lighthouse.

**Phase relevance:** Design system phase, font configuration step. Should be done early since fonts affect all text sizing and layout.

---

### Pitfall 7: Experiment Table-to-Card Redesign Loses Comparison Capability

**What goes wrong:** The current ExperimentTable renders experiments in a sortable table with columns for ID, hypothesis, accuracy across 3 validation years, log loss, and status. Users can sort by accuracy to find the best experiment, scan across rows to compare experiments, and click to expand details. If this is redesigned as a card grid (per the v1.2 "experiments page redesign" goal), the ability to compare experiments side-by-side is lost. Cards are good for browsing individual items but bad for comparing values across items.

**Why it happens:** Cards feel more modern and visually rich. The v1.2 goal mentions "full descriptions, proper column alignment" which suggests the current truncated hypothesis display is inadequate. The natural instinct is to give each experiment more visual space via cards. But experiments are fundamentally comparison data, not browse data.

**Consequences:** Users can no longer quickly answer "which experiment had the highest accuracy?" without mentally holding values from multiple cards. The sort functionality becomes less useful because cards do not align values vertically. Information density drops -- the current table shows 7 columns of data in a single scannable row; a card would need to stack these vertically, showing fewer experiments per viewport.

**Prevention:**
1. Keep the table as the primary view for experiments. Tables are the correct UI pattern for comparison data with consistent fields.
2. Improve the table rather than replacing it: show full hypothesis text (not truncated), add proper column alignment, improve the expanded detail view.
3. If the redesign adds a card-style detail panel, make it an enhancement to the table (click a row to open a side panel or expanded section) rather than a replacement.
4. If cards are truly desired, implement a toggle: table view (default) and card view (optional). Default to table because experiment comparison is the primary use case.
5. The "full descriptions" goal can be achieved within the table by making the hypothesis column wider and allowing text wrap instead of truncation at 60 characters.

**Detection:** After redesign, ask: "Can a user compare the accuracy of experiments 3 and 5 without scrolling?" If no, the redesign lost information density.

**Phase relevance:** Experiments page redesign phase. The key decision (table vs. cards vs. hybrid) must be made before any implementation.

---

### Pitfall 8: Sidebar Navigation Does Not Update for New Routes

**What goes wrong:** The Sidebar component has a hardcoded `navItems` array with four entries: This Week (`/`), Accuracy (`/accuracy`), Experiments (`/experiments`), History (`/history`). When the landing page moves This Week to `/picks`, the sidebar nav link must update from `/` to `/picks`. If forgotten, the sidebar "This Week" link points to the landing page. Additionally, the `end={item.to === "/"}` prop on NavLink (which prevents the root path from matching all routes) must be reconsidered since `/` is no longer a dashboard route.

**Why it happens:** Navigation is often the last thing updated because developers focus on the page content and routing logic. The hardcoded nav array is easy to overlook.

**Consequences:** Clicking "This Week" in the sidebar navigates to the landing page (which has a different layout). The active state highlighting breaks -- if the user is on `/picks`, no sidebar item is highlighted because none matches that path. The mobile top nav has the same issue (it uses the same `navItems` array).

**Prevention:**
1. Update `navItems` in `Sidebar.tsx` immediately when routes change. Change `{ to: "/", icon: Calendar, label: "This Week" }` to `{ to: "/picks", ... }` (or whatever the new path is).
2. Remove the `end={item.to === "/"}` special case since no nav item points to `/` anymore.
3. Consider whether the sidebar should have a "Home" link to the landing page, or if the brand name in the sidebar header should link to `/`.
4. Test the mobile top nav (lines 85-107 of `Sidebar.tsx`) separately -- it renders the same `navItems` but has different layout constraints.

**Detection:** After route changes, click every sidebar link on both desktop and mobile viewports. Verify the active state (blue highlight) appears on the correct item for each page.

**Phase relevance:** Route restructuring phase, immediately after defining the new route structure.

---

### Pitfall 9: Off-Season Default Routing Creates an Empty State Trap

**What goes wrong:** The v1.2 requirements mention "off-season-aware default routing (Home instead of empty This Week)." During the NFL off-season (roughly February through September), This Week has no predictions to show -- it displays an empty or error state. The plan is to route to the landing page instead. But this conditional routing is complex: it requires knowing whether the current date falls within the NFL season, which means either hardcoding season dates (fragile -- the NFL schedule varies) or checking the API for current predictions (adds a loading state and potential error to the routing decision).

**Why it happens:** The NFL off-season is 7+ months. The current dashboard shows an empty This Week page for most of the year, which is a poor first impression. The desire to fix this is correct, but the implementation is tricky.

**Consequences:** If the routing check fails (API error, slow response), the user sees a loading spinner before being routed anywhere. If season dates are hardcoded, they must be updated annually. If the logic has a bug, users during the season get sent to the landing page instead of picks, or off-season users are stuck on an empty picks page.

**Prevention:**
1. Simplest approach: always make `/` the landing page, never conditionally route. The landing page has a CTA button "View This Week's Picks" that goes to `/picks`. During the off-season, `/picks` shows a friendly "The NFL season starts in September. Check back then!" message with links to History and Experiments.
2. If conditional routing is truly wanted, implement it client-side in the LandingPage component: fetch current predictions, if data exists show a banner "This week's picks are live! [View Picks]", if not show the standard landing page content. This avoids routing-level complexity.
3. Do NOT make the router itself depend on an API call. The route structure should be static and predictable.
4. The off-season empty state on `/picks` should be a designed component, not a loading error or blank page. It should show the most recent completed season's stats and a link to History.

**Detection:** Test the full flow during off-season: navigate to `/`, click to `/picks`, see the off-season state. Test during the season: navigate to `/`, click to `/picks`, see live predictions. Both should feel intentional.

**Phase relevance:** Landing page phase. The routing strategy must be decided before building the landing page content.

---

### Pitfall 10: Production nginx Config Needs No Changes But Catch-All Route Needs One

**What goes wrong:** The existing nginx config (`docker/nginx.conf`) has `try_files $uri $uri/ /index.html` which correctly serves `index.html` for all non-file client-side routes. This means adding `/picks` to React Router will work without any nginx changes -- nginx serves `index.html`, React Router handles the path. However, the app currently has NO catch-all route for 404s. If a user navigates to `/nonexistent`, React Router renders nothing (blank page within the layout). With the new landing page at `/`, this becomes more visible because users might type partial URLs.

**Why it happens:** The existing route structure was simple enough that invalid paths were unlikely. With more routes and a public-facing landing page, the surface area for invalid URLs increases.

**Consequences:** Users hitting typo URLs see a blank content area with a sidebar. No feedback that the page does not exist. Search engines crawling broken links index blank pages.

**Prevention:**
1. Add a catch-all route at the end of the route configuration:
   ```tsx
   <Route path="*" element={<NotFoundPage />} />
   ```
2. Place it inside the `AppLayout` wrapper so it has the sidebar context (or in `LandingLayout` depending on desired 404 appearance).
3. The `NotFoundPage` should link to `/` (landing page) and `/picks` (dashboard).
4. No nginx changes needed -- the existing `try_files` correctly serves index.html for all paths.

**Detection:** Navigate to `/asdfgh` and verify a proper 404 page appears instead of blank content.

**Phase relevance:** Route restructuring phase. Add alongside the route changes.

---

## Minor Pitfalls

---

### Pitfall 11: Google Fonts @import Blocks CSS Parsing

**What goes wrong:** The current `index.css` starts with `@import url('https://fonts.googleapis.com/...')`. CSS `@import` of an external URL is render-blocking: the browser must fetch the external stylesheet before it can continue parsing the rest of the CSS file. This adds 50-200ms to first paint on every cold load. If the Google Fonts CDN is slow or unreachable, the entire page rendering stalls.

**Prevention:**
1. When migrating to the new font, move the font loading to `<link>` tags in `index.html` (with `rel="preload"`) instead of CSS `@import`.
2. Better: self-host the fonts as WOFF2 and use `@font-face` declarations directly in CSS, eliminating the external dependency entirely.
3. If keeping Google Fonts temporarily, at minimum move from `@import` to a `<link>` tag in `index.html`, which can be loaded in parallel with other resources.

**Phase relevance:** Design system phase, font migration step.

---

### Pitfall 12: oklch Browser Compatibility for Custom Palette Values

**What goes wrong:** The existing shadcn/ui variables already use oklch (e.g., `--background: oklch(0.145 0 0)`), so the codebase is committed to oklch. The silverreyes.net palette colors must be converted to oklch values to match. If the designer provides colors in hex/HSL/RGB, the conversion to oklch must preserve the intended appearance. oklch values are not intuitive -- `oklch(0.7 0.15 250)` does not map obviously to a recognizable color. Conversion errors produce unexpected hues.

**Prevention:**
1. Use the oklch color picker (oklch.com) or Tailwind's built-in color tools to convert brand colors accurately.
2. Verify converted colors visually in the browser, not just numerically.
3. oklch's Lightness (L) channel must stay above 0.1 for dark backgrounds and below 0.95 for light text to maintain WCAG contrast ratios.
4. Test contrast ratios explicitly: `--foreground` against `--background`, `--primary-foreground` against `--primary`. Use a contrast checker that supports oklch.

**Phase relevance:** Design system phase, palette definition step.

---

### Pitfall 13: Collapsible Table Row Rendering Breakage After Style Changes

**What goes wrong:** The ExperimentTable uses shadcn/ui's `Collapsible` component with a `render` prop to inject `<TableRow>` elements: `<CollapsibleTrigger render={<TableRow className="hover:bg-zinc-800/50 cursor-pointer transition-colors" />}>`. This is a non-standard usage pattern where the Collapsible wraps table rows. Changing the table's styling (background colors, hover states, border patterns) can break the visual continuity between the trigger row and the expanded content row. Additionally, this pattern uses `@base-ui/react` primitives (not Radix) -- the render prop API is specific to base-ui and behaves differently from Radix's `asChild`.

**Prevention:**
1. When updating the experiment table styles, test the expand/collapse interaction specifically. The expanded row (`bg-zinc-900/50`) must visually connect to its parent row.
2. Update both the trigger row and content row backgrounds together -- they are separate elements that need coordinated styling.
3. Do not attempt to refactor the Collapsible-in-Table pattern during the style migration. It works and is fragile. Style it in place.

**Phase relevance:** Experiments page redesign phase.

---

### Pitfall 14: Tooltip Portal Z-Index Conflicts with New Landing Page Elements

**What goes wrong:** The current tooltip implementation uses `TooltipPrimitive.Portal` to render tooltips in a portal (outside the component tree in the DOM). Portaled elements rely on z-index stacking. The landing page will introduce new full-width sections, potentially with sticky headers or hero overlays. If these have z-index values that compete with the tooltip's `z-50`, tooltips on the dashboard pages can render behind landing page elements during transitions, or the landing page's own interactive elements can conflict.

**Prevention:**
1. The landing page and dashboard are on different routes and will not render simultaneously, so this is mainly a risk during route transitions or if shared components (like a global header) use z-index.
2. If adding a sticky navigation to the landing page, use `z-40` or lower. Reserve `z-50` for tooltips and modals.
3. Audit all z-index values before adding new ones. The current codebase uses `z-50` for the mobile nav and tooltips.

**Phase relevance:** Landing page phase, specifically any sticky/fixed-position elements.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Design System: Palette Migration | Hardcoded color classes (48 across 16 files) not affected by CSS variable changes (Pitfall 1) | Create semantic tokens first, migrate hardcoded refs, then swap palette values |
| Design System: CSS Variables | Custom token names colliding with shadcn/ui's --accent, --primary, etc. (Pitfall 4) | Either namespace custom tokens (--brand-*) or deliberately map palette to shadcn/ui semantics |
| Design System: @theme inline | New colors defined directly in @theme inline cannot be overridden for dark mode (Pitfall 5) | Always use the :root -> var() -> @theme inline indirection pattern |
| Design System: Fonts | FOUT/FOIT from external font loading; @import blocks CSS parsing (Pitfalls 6, 11) | Self-host WOFF2, preload in index.html, use font-display: swap |
| Design System: oklch Colors | Hex-to-oklch conversion errors produce wrong hues, contrast violations (Pitfall 12) | Visual verification, contrast ratio checks |
| Route Restructuring | Root path change breaks existing bookmarks, sidebar nav stale (Pitfalls 2, 8) | Update Sidebar navItems, add redirects, test all bookmark paths |
| Route Restructuring | No catch-all 404 route (Pitfall 10) | Add path="*" route with NotFoundPage |
| Landing Page: Layout | Landing page inherits sidebar margin from AppLayout (Pitfall 3) | Use separate LandingLayout, sibling route groups |
| Landing Page: Off-Season | Conditional routing based on season status is complex and fragile (Pitfall 9) | Static routes, handle off-season as designed empty state on /picks |
| Landing Page: Z-Index | Sticky/fixed elements conflict with tooltip portals (Pitfall 14) | Reserve z-50+ for overlays; audit z-index before adding |
| Experiments Redesign | Table-to-card conversion loses comparison capability (Pitfall 7) | Improve the table, don't replace it; cards for detail, table for comparison |
| Experiments Redesign | Collapsible-in-table render prop pattern is fragile (Pitfall 13) | Style in place, don't refactor the pattern during migration |

---

## Sources

- **Codebase inspection:** Direct analysis of `index.css`, `App.tsx`, `Sidebar.tsx`, `AppLayout.tsx`, `PickCard.tsx`, `ExperimentTable.tsx`, `card.tsx`, `badge.tsx`, `tooltip.tsx`, `nginx.conf`, `docker-compose.yml`, `package.json`, `vite.config.ts` and all 16 files with hardcoded color references. HIGH confidence.
- **Tailwind v4 theming:** [Theme variables docs](https://tailwindcss.com/docs/theme), [@theme vs @theme inline discussion](https://github.com/tailwindlabs/tailwindcss/discussions/18560), [Theming best practices in v4](https://github.com/tailwindlabs/tailwindcss/discussions/18471). HIGH confidence.
- **shadcn/ui theming:** [Theming docs](https://ui.shadcn.com/docs/theming), [Tailwind v4 migration](https://ui.shadcn.com/docs/tailwind-v4), [Customizing themes without breaking updates](https://medium.com/@sureshdotariya/customizing-shadcn-ui-themes-without-breaking-updates-a3140726ca1e). HIGH confidence.
- **Font loading:** [Ultimate guide to font loading optimization](https://onenine.com/ultimate-guide-to-font-loading-optimization/), [Self-host Google Fonts for better Core Web Vitals](https://www.corewebvitals.io/pagespeed/self-host-google-fonts), [Web font optimization guide](https://font-converters.com/guides/web-font-optimization). MEDIUM confidence (general best practices, not project-specific).
- **Table vs. card UX:** [Table vs List View vs Card Grid](https://uxpatterns.dev/pattern-guide/table-vs-list-vs-cards), [Cards versus Table UX Patterns](https://cwcorbin.medium.com/redux-cards-versus-table-ux-patterns-1911e3ca4b16), [Enterprise data tables](https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-data-tables). MEDIUM confidence.
- **React Router v7:** [Upgrading from v6](https://reactrouter.com/upgrading/v6), [React Router SPA docs](https://reactrouter.com/how-to/spa). HIGH confidence.
- **nginx SPA routing:** [How to fix 404 errors with React Router and Nginx](https://www.frontendundefined.com/posts/tutorials/nginx-react-router-404/), [Configure React Router with Nginx](https://oneuptime.com/blog/post/2025-12-16-nginx-react-router-configuration/view). HIGH confidence.
