# Project Research Summary

**Project:** NFL Game Predictor (Nostradamus) — v1.2 Design & Landing Page
**Domain:** Design system migration, public landing page, and experiments page redesign for an existing React dashboard
**Researched:** 2026-03-24
**Confidence:** HIGH

## Executive Summary

The v1.2 milestone is a frontend-only effort touching three distinct workstreams: aligning the dashboard's visual design with the silverreyes.net parent brand, adding a public-facing landing page, and redesigning the experiments page for better readability. All research confirms that the existing stack (React 19 + Vite 7 + Tailwind v4 + shadcn/ui) is already well-suited for these goals. The only new dependencies are two Fontsource packages for self-hosted fonts; everything else is CSS variable changes, routing adjustments, and new or modified React components. No backend changes are required.

The recommended approach follows a strict dependency chain: design tokens must be defined and all hardcoded color references migrated before any visual page work begins. Both the landing page and the experiments redesign build on the same token layer, so they can proceed in parallel once the design system phase is complete. The key architectural decision — placing the landing page outside AppLayout as a separate full-width route — is clear-cut and well-supported by React Router v7's nested route structure.

The primary risk is the 48 hardcoded Tailwind color utility classes scattered across 16 files that bypass the CSS variable system. If the palette is swapped before these are migrated to semantic tokens, the dashboard will visually split between components that respond to the new palette and those that do not. The prevention strategy is established: define semantic tokens first, migrate all hardcoded references in a single dedicated pass, then swap the underlying palette values. A secondary risk is the experiments page redesign losing comparison capability if tables are replaced with cards outright; research recommends improving the table rather than replacing it, or using a hybrid approach.

## Key Findings

### Recommended Stack

The existing stack requires no structural changes. Only two new npm packages are needed: `@fontsource/syne` and `@fontsource/ibm-plex-mono`, which self-host the fonts matching the silverreyes.net brand identity and eliminate the current render-blocking Google Fonts CDN import. All other changes are CSS variable overrides in `src/index.css` and React component additions. See `.planning/research/STACK.md` for full details.

**Core technologies:**
- `@fontsource/syne` + `@fontsource/ibm-plex-mono`: Self-hosted display and mono fonts — eliminates the render-blocking Google Fonts `@import`, bundles fonts into the Vite build, matches silverreyes.net typographic identity
- `tw-animate-css` (already installed): Hero entrance animations — covers all needed fade/slide/stagger effects without adding Framer Motion (~30KB savings)
- shadcn/ui CSS variable system (already installed): Zero-component-code theme migration — the entire dashboard re-themes by changing `:root` and `.dark` CSS variable values in `index.css`
- `react-router` v7 (already installed): Two-layout routing pattern — supports sibling route groups cleanly, no new packages needed for the full-width LandingLayout pattern

**Critical version note:** Tailwind v4 eliminated `tailwind.config.ts` in favor of CSS-first `@theme` directives. All theme customization must go through `index.css`. Adding a config file would create a v3/v4 hybrid that breaks tooling.

### Expected Features

Research classifies features into must-ship for v1.2 and items to defer. See `.planning/research/FEATURES.md` for the full prioritized table.

**Must have (table stakes):**
- Design system token migration to silverreyes.net warm amber palette — without this, the subdomain feels disconnected from the parent brand
- Landing page with hero (headline + accuracy stat), how-it-works 3-step explainer, and explore CTAs — this is the new front door; the current off-season empty state as entry point is unacceptable
- Route restructure: `/` to landing page, `/this-week` to ThisWeekPage — permanently solves the off-season routing problem
- Accent color and border token migration across all components — replaces all hardcoded `blue-400`/`zinc-800` references with semantic tokens
- Experiments page: full hypothesis text display and improved layout — the current 60-char truncation cuts off the most important context per experiment

**Should have (differentiators):**
- Live hero stat from API (current accuracy from `useModelInfo` hook, falls back to static gracefully)
- Delta from previous best on experiment cards (`prev_best_acc` field already exists in the response type)
- Smooth theme transition (`transition: background-color 0.2s` on body/cards)
- Sidebar "Home" link and updated branding

**Defer to v1.3+:**
- Theme toggle (dark/light): requires defining complete light-mode token set and testing all components; ship dark-only for v1.2
- Spread experiments display: requires new API endpoint and different metric schemas (accuracy vs MAE)
- Experiment timeline visualization: polish feature; table/card improvement is the priority
- Animated scroll transitions for how-it-works: CSS-only addition that can be layered on after content is finalized

### Architecture Approach

The migration follows a single-file-of-truth CSS strategy. All theming (palette variables, font mappings, spacing tokens) lives exclusively in `src/index.css` via the existing `:root` / `.dark` / `@theme inline` structure. New components are additive: one new page directory (`components/home/`) and four home section components, plus replacement experiment card components. The existing API layer, hooks, and TypeScript types require no changes. See `.planning/research/ARCHITECTURE.md` for full component inventory and post-v1.2 file structure.

**Major components:**
1. `HomePage.tsx` (new) — landing page, full-width layout outside AppLayout, orchestrates hero/how-it-works/CTAs/footer sections
2. Bare route outside AppLayout (routing change) — prevents the `md:ml-[180px]` sidebar margin from being applied to the full-width landing page
3. `ExperimentCard.tsx` + `ExperimentDetailPanel.tsx` (new) — replace the cramped collapsible-in-table pattern with a card grid and inline detail expansion
4. `index.css` (modified) — single point of change for the entire theme migration: remove Google Fonts import, add Fontsource imports, replace `:root`/`.dark` oklch values with warm amber palette, update `@theme inline` font mappings
5. `Sidebar.tsx` (modified) — add Home nav item, update `navItems` paths, replace 8 hardcoded color references with semantic tokens
6. `App.tsx` (modified) — route restructure to place landing page outside AppLayout wrapper

### Critical Pitfalls

Top pitfalls extracted from `.planning/research/PITFALLS.md`:

1. **Hardcoded color classes bypass the theme system** — 48 utility classes across 16 files (e.g., `bg-zinc-900`, `text-blue-400`, `border-zinc-800`) are not CSS variable-backed and will not respond to palette changes. Define semantic tokens first, migrate all 48 references in a dedicated pass, then swap palette values. Never swap palette first or the dashboard visually splits into two different apps.

2. **Landing page wrapped inside AppLayout inherits sidebar margin** — AppLayout applies `md:ml-[180px]` to `<main>`. A landing page nested inside it gets a phantom left margin and sidebar chrome. Use two sibling route groups at the top level — one for Home (no layout wrapper), one for dashboard pages inside AppLayout. Never conditionally hide the sidebar inside AppLayout.

3. **Route restructure stales the sidebar nav** — The Sidebar `navItems` array currently has `{ to: "/", label: "This Week" }`. When the root path moves to the landing page, this link points to the wrong page and the active-state highlight breaks for all dashboard routes. Update `navItems` immediately alongside the route change.

4. **Table-to-card conversion loses comparison capability** — Experiments are comparison data. Replacing the table with pure cards removes the ability to scan across rows to compare accuracy values. Improve the existing table (show full hypothesis text, fix column alignment) and use the card pattern only for the expanded detail view.

5. **Direct oklch values in `@theme inline` break dark mode** — Variables defined with literal color values inside `@theme inline` (not via `var()`) cannot be overridden in `.dark`. Always follow the established indirection: raw variable in `:root` and `.dark`, then `var()` reference in `@theme inline`. Audit for any literal oklch values not wrapped in `var()`.

## Implications for Roadmap

Based on the combined research, three sequential phases emerge from the dependency analysis. Theme must precede pages; routing restructure can accompany or precede theme work since it is purely structural; landing page and experiments redesign are independent once routing and theme are complete.

### Phase 1: Design System Foundation
**Rationale:** Every visual component in the dashboard reads from CSS variables. The landing page and experiments redesign both consume the new token layer. Building either page before the theme is defined means using old tokens and reworking later or hardcoding values that should come from variables. This phase must complete before any visual page work begins.
**Delivers:** Complete warm amber design system token set in `index.css`; self-hosted Syne + IBM Plex Mono fonts replacing Google Fonts CDN; all 48 hardcoded color references migrated to semantic tokens; existing dashboard pages visually aligned with silverreyes.net palette.
**Addresses:** CSS custom property migration, typography alignment, accent color consistency, border token migration (FEATURES.md table stakes)
**Avoids:** Pitfall 1 (hardcoded colors resist theme changes), Pitfall 5 (`@theme inline` dark mode incompatibility), Pitfall 6 (font FOUT), Pitfall 11 (Google Fonts render blocking), Pitfall 12 (oklch conversion errors)
**Research flag:** Standard patterns — shadcn/ui theming, Tailwind v4 `@theme inline`, and Fontsource font loading are thoroughly documented with official sources. No deeper research needed.

### Phase 2: Route Restructure and Navigation
**Rationale:** The routing change is a prerequisite for building the landing page. It is a small, low-risk change (5 lines in `App.tsx`, 3 lines in `Sidebar.tsx`) that can be done immediately after or alongside Phase 1. Completing it before building page content ensures the infrastructure is in place and testable.
**Delivers:** `/` routes to full-width landing page (no sidebar); dashboard pages move to `/this-week`, `/accuracy`, etc.; Sidebar gains Home nav item; catch-all 404 route added; nginx requires no changes (existing `try_files $uri $uri/ /index.html` already handles all client-side routes).
**Addresses:** Off-season default routing, Sidebar Home link (FEATURES.md table stakes)
**Avoids:** Pitfall 2 (route breaks existing bookmarks), Pitfall 3 (sidebar margin on landing page), Pitfall 8 (stale sidebar nav), Pitfall 10 (missing 404 catch-all)
**Research flag:** Standard patterns — React Router v7 nested routes are well-documented. No deeper research needed.

### Phase 3: Landing Page
**Rationale:** Depends on both Phase 1 (design tokens) and Phase 2 (routing infrastructure). Can proceed in parallel with Phase 4 once those foundations are in place. This is the primary external-facing deliverable of v1.2 — the new front door visible to all visitors, solving the off-season empty-state problem permanently.
**Delivers:** Hero section (headline + live accuracy stat from `useModelInfo` hook with static fallback), how-it-works 3-step explainer, explore CTAs card grid linking to dashboard sections, model credential summary stats, responsive mobile-first layout, tw-animate-css entrance animations.
**Implements:** `HomePage.tsx`, `HeroSection.tsx`, `HowItWorksSection.tsx`, `ExploreCTAs.tsx`, `HomeFooter.tsx`
**Avoids:** Pitfall 3 (dual layout — landing page is outside AppLayout), Pitfall 9 (no conditional routing — landing page always shows at `/`; off-season state is a designed empty state on `/this-week`), Pitfall 14 (z-index conflicts — reserve `z-50+` for tooltips and modals, use `z-40` or lower for sticky nav elements)
**Research flag:** Standard patterns — hero sections, how-it-works layouts, and CTA grids are well-documented UX patterns. No deeper research needed.

### Phase 4: Experiments Page Redesign
**Rationale:** Independent of Phase 3 once Phases 1 and 2 are complete. The current ExperimentTable has three problems: 60-char hypothesis truncation, cramped multi-column layout, and no visual distinction for the kept experiment. The redesign must preserve comparison capability while improving readability.
**Delivers:** Full hypothesis text displayed without truncation; improved layout with proper column structure; card-style expanded detail view below the table or inline; left accent border visual distinction for kept vs. reverted experiments; delta from previous best (`prev_best_acc` field already in `ExperimentResponse` type).
**Implements:** `ExperimentCard.tsx`, `ExperimentCardGrid.tsx`, `ExperimentDetailPanel.tsx` (new); `ExperimentTable.tsx`, `ExperimentDetail.tsx` (removed or retained in hybrid approach)
**Avoids:** Pitfall 7 (table-to-card loses comparison capability — improve the table, use cards only for detail), Pitfall 13 (fragile collapsible-in-table render prop pattern — style in place, do not refactor during migration)
**Research flag:** The table vs. card vs. hybrid UI decision must be resolved explicitly before implementation. FEATURES.md describes card-based redesign; PITFALLS.md warns against it for comparison data. This is the highest-ambiguity design decision in the milestone.

### Phase Ordering Rationale

- Phase 1 (theme) must be first because every subsequent page uses the new token layer; building pages before the theme creates double-work
- Phase 2 (routing) can overlap with Phase 1 since it is purely structural TypeScript; it must complete before Phase 3 can be tested end-to-end
- Phases 3 and 4 are independent workstreams that can proceed in parallel; they share no component dependencies
- The entire milestone is frontend-only; no backend changes block any phase

### Research Flags

Phases needing explicit design decision before implementation:
- **Phase 4 (Experiments Redesign):** The table vs. card vs. hybrid UI pattern decision must be made before building. Resolve during requirements/roadmap phase by picking one approach and committing to it.

Phases with standard, well-documented patterns (no deeper research needed):
- **Phase 1 (Design System):** shadcn/ui CSS variable theming, Tailwind v4 `@theme inline`, and Fontsource font loading are all thoroughly documented with official sources at HIGH confidence.
- **Phase 2 (Routing):** React Router v7 nested routes and layout patterns are standard and well-documented.
- **Phase 3 (Landing Page):** Hero sections, how-it-works patterns, and CTA grids are established UX patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations based on direct `package.json` + `index.css` inspection plus official Tailwind v4, shadcn/ui, and Fontsource docs |
| Features | MEDIUM-HIGH | Based on codebase analysis + silverreyes.net inspection + UX research patterns; actual silverreyes.net CSS token values could not be fully extracted (design tokens inferred from variable names, not direct CSS read) |
| Architecture | HIGH | Based on direct inspection of all 40+ source files plus official React Router v7 and Tailwind v4 docs; recommended patterns are the documented intended use |
| Pitfalls | HIGH | Most pitfalls identified from direct codebase analysis (exact file counts, line numbers, class names verified); validated against official docs and community discussions |

**Overall confidence:** HIGH

### Gaps to Address

- **Exact silverreyes.net oklch palette values:** ARCHITECTURE.md notes that the actual OKLCH values could not be fully extracted — only variable names were confirmed. STACK.md provides a reference palette (`--amber-accent: oklch(0.767 0.157 71.7)` / `#f0a020`) based on inspection, but these should be verified against the live site at the start of Phase 1 before committing to the design system values.
- **Exact font used on silverreyes.net:** ARCHITECTURE.md used Space Grotesk as a placeholder; STACK.md identifies the font as Syne after direct inspection. Confirm Syne is correct at implementation start before installing Fontsource packages.
- **Experiments table vs. card vs. hybrid decision:** Research gives conflicting guidance — FEATURES.md describes a card-based redesign; PITFALLS.md warns it loses comparison capability. Resolve with an explicit decision in the requirements document before Phase 4 begins.
- **Theme toggle scope for v1.2:** Deferring the dark/light toggle is recommended, but this should be confirmed in the requirements document since it affects whether light-mode tokens need to be fully specified in Phase 1 (they do not if dark-only is confirmed).

## Sources

### Primary (HIGH confidence)
- `frontend/src/index.css` (direct file read) — current theme variable structure, 136 lines
- `frontend/package.json` (direct file read) — current dependency versions
- All 40+ `frontend/src/` source files (direct inspection) — component inventory, hardcoded color audit, routing structure
- [shadcn/ui Theming Docs](https://ui.shadcn.com/docs/theming) — CSS variable structure, oklch format
- [shadcn/ui Tailwind v4 Guide](https://ui.shadcn.com/docs/tailwind-v4) — `@theme inline` pattern, v4-specific integration
- [Tailwind CSS v4 Theme Variables](https://tailwindcss.com/docs/theme) — `@theme` directive, CSS-first configuration
- [React Router v7 Routing](https://reactrouter.com/start/framework/routing) — nested routes, layout routes, index routes
- [tw-animate-css GitHub](https://github.com/Wombosvideo/tw-animate-css) — available animation utilities, composable classes

### Secondary (MEDIUM confidence)
- silverreyes.net (live site inspection via WebFetch) — design tokens, CSS variable naming, typography; oklch values inferred, not directly extractable
- [@fontsource/syne](https://www.npmjs.com/package/@fontsource/syne) + [@fontsource/ibm-plex-mono](https://www.npmjs.com/package/@fontsource/ibm-plex-mono) — font weights and self-hosting patterns
- [web.dev Font Best Practices](https://web.dev/articles/font-best-practices) — self-hosting recommendation for performance
- [LogRocket Hero Section Best Practices](https://blog.logrocket.com/ux-design/hero-section-examples-best-practices/) — landing page UX patterns
- [UX Patterns Dev — Table vs Cards](https://uxpatterns.dev/pattern-guide/table-vs-list-vs-cards) — comparison data UI guidance
- [Enterprise Data Tables](https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-data-tables) — experiment table UX considerations

### Tertiary (LOW confidence)
- [Tailwind CSS v4 Theming Discussion](https://github.com/tailwindlabs/tailwindcss/discussions/18471) — community patterns for multi-theme v4 (community thread, not official docs)

---
*Research completed: 2026-03-24*
*Ready for roadmap: yes*
