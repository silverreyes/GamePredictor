# Feature Landscape

**Domain:** Design system migration, landing page, and experiment scoreboard redesign for NFL prediction dashboard
**Researched:** 2026-03-24
**Milestone:** v1.2 Design & Landing Page
**Confidence:** MEDIUM-HIGH (based on analysis of existing codebase, silverreyes.net design system, UX research patterns, and web search verification)

---

## Table Stakes

Features users expect for a design refresh milestone. Missing = the redesign feels half-done.

### Landing Page

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Hero section with headline + stat | Visitors decide in <5 seconds whether to stay; the hero must answer "what does this do?" instantly | Low | Headline: "Nostradamus" or project name. Sub-headline: one-sentence value prop. Hero stat: "63.7% accuracy" as the proof point. No image needed -- the stat IS the visual. |
| How-it-works explainer (3 steps) | Non-technical visitors need to understand the ML pipeline without jargon; this is the standard pattern for technical product landing pages | Medium | Three steps: (1) Ingest 20 seasons of data, (2) Train models on team stats, (3) Predict next week's winners. Use icons, short labels, and 1-2 sentence descriptions. Avoid words like "XGBoost" or "feature engineering" -- say "pattern recognition" and "team performance signals." |
| Explore CTAs linking to dashboard views | A landing page without navigation into the product is a dead end; visitors need clear paths to the actual predictions | Low | 2-4 cards linking to This Week, Accuracy, Experiments, History. Use descriptive labels: "See This Week's Picks," "Track Season Accuracy," etc. |
| Model credential summary | Users evaluate trust through numbers; showing key metrics (accuracy, games predicted, seasons of data) builds credibility without requiring users to dig | Low | 3-4 stat cards: accuracy percentage, total games predicted, seasons of historical data, models compared. These are static or API-fed numbers. |
| Responsive layout (mobile-first) | silverreyes.net is responsive; a subdomain that breaks on mobile undermines the parent brand | Low | Single-column stack on mobile, multi-column grid on desktop. Hero headline + stat must be visible without scrolling on any device. |

### Design System Alignment

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| CSS custom property migration to silverreyes.net tokens | The dashboard currently uses shadcn/ui's default oklch color tokens; silverreyes.net uses semantic tokens (`--color-text`, `--color-accent`, `--color-surface`, `--color-border`). Mismatched palettes make the subdomain feel disconnected. | Medium | Map shadcn's `--foreground`, `--muted-foreground`, `--card`, `--border` to silverreyes.net equivalents. The `@theme inline` block in `index.css` is the single point of change. |
| Typography alignment (display + mono fonts) | silverreyes.net uses `--font-display` for headings and `--font-mono` for metadata/labels. Dashboard currently uses Inter + JetBrains Mono. Must either adopt the parent fonts or ensure the pairing feels cohesive. | Low | If silverreyes.net's `--font-display` is a different family, import it. JetBrains Mono already serves the `--font-mono` role well. Key: headings should match the parent site's typographic voice. |
| Dark mode as default with light toggle support | silverreyes.net defaults to dark with localStorage-persisted `data-theme` toggle. The dashboard is currently dark-only (hardcoded `.dark` class). Must at minimum keep dark as primary; light mode toggle is a bonus. | Low-Med | The `.dark` class in `index.css` already defines dark tokens. Adding `data-theme="light"` support requires defining the light variant tokens to match silverreyes.net. Can ship dark-only initially and add toggle later. |
| Accent color consistency | silverreyes.net uses `--color-accent` for hover states, links, and interactive highlights. The dashboard currently uses hardcoded `blue-400`/`blue-500` classes throughout (Sidebar active state, ConfidenceBadge, SHAP bars). | Medium | Replace all hardcoded blue Tailwind classes with a semantic `--color-accent` token. This is scattered across ~8 components (Sidebar, PickCard, ExperimentDetail, SummaryCards, SpreadLabel, etc.). |
| Spacing and border patterns | silverreyes.net uses `--space-xs/sm/md/lg` tokens and consistent border styling. The dashboard uses mixed Tailwind spacing (`p-3`, `p-4`, `p-6`, `p-8`) and hardcoded border colors (`border-zinc-800`). | Low | Define spacing tokens in `@theme inline`. Replace hardcoded `zinc-800` border colors with `var(--color-border)`. This is mostly a find-and-replace operation. |
| Card component visual alignment | silverreyes.net project cards use left accent bars with hover animation (height 0 -> full). Dashboard cards use shadcn Card with left border-l-3px for confidence tier. The patterns are compatible but need palette alignment. | Low | Keep shadcn Card wrapper. Update tier border colors from hardcoded `blue-500`/`amber-500`/`zinc-500` to design-system-aware equivalents. The left-accent pattern already exists in both systems. |

### Off-Season Default Routing

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Route to landing page (Home) instead of empty This Week | Currently, the index route (`/`) maps to ThisWeekPage, which shows a generic "Offseason" ErrorState during the 6+ months with no games. This is the first thing any visitor sees. A blank error page as the front door is unacceptable. | Low | Change the route structure: `/` -> new LandingPage, `/this-week` -> ThisWeekPage. Update Sidebar navItems. The landing page always has content regardless of season state. |
| Sidebar "Home" link | With a landing page at `/`, the sidebar needs a Home entry. Currently missing because ThisWeekPage was the de facto home. | Low | Add Home icon (e.g., `Home` from lucide-react) to navItems array. Straightforward 3-line change in Sidebar.tsx. |

### Experiments Page Redesign

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Full hypothesis text (not truncated) | The current table truncates hypotheses at 60 chars with "..." -- the hypothesis IS the experiment's purpose and users need to read it to understand what was tested | Low | Remove the `.slice(0, 60)` truncation. Display full text in the table row or in the expanded detail. |
| Proper column alignment | Current table has 7 columns crammed into a responsive layout with fixed widths (`w-12`, `w-[100px]`, `w-20`). On narrow viewports, columns overflow or compress awkwardly. | Medium | Switch from a dense multi-column table to a card-based or two-column layout. Each experiment gets a row/card with the hypothesis prominently displayed and metrics in a structured grid below. |
| Expanded detail with parameters, features, SHAP | The current `ExperimentDetail` component already exists and shows hypothesis, params, features, and SHAP top-5 bars. But the expand/collapse via `Collapsible` inside a `<Table>` is fragile (table row semantics + collapsible conflict). | Medium | Keep the existing data display (it works). Rethink the container: use a card with collapsible section instead of table rows with collapsible. Preserves all existing ExperimentDetail content. |
| Visual distinction between kept and reverted experiments | Current Badge with green/red is good but small. Users scanning the list need to instantly see which experiments were promoted vs discarded. | Low | Add a left accent border (green for kept, muted for reverted) matching the card pattern from silverreyes.net. Badge remains but the visual weight increases. |

---

## Differentiators

Features that set the redesign apart. Not expected, but valued.

### Landing Page -- Advanced

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Live hero stat from API | Instead of a hardcoded "63.7%", fetch the actual current accuracy from `/api/model/info`. Shows the system is alive and updating. | Low | Single API call. Falls back to static text if API is down. The useModelInfo hook already exists. |
| "Model vs Baselines" visual comparison | A simple bar chart or comparison showing model accuracy vs "always pick home team" and "always pick better record" baselines. This is the credibility proof visitors need. | Medium | Three horizontal bars with labels. Can be pure CSS (no charting library needed). Data from modelInfo endpoint. |
| Season-at-a-glance mini stats | Show current season record (e.g., "142-98") with a win percentage badge. Gives visitors a sense of volume and recency. | Low | Data from prediction history endpoint. Single summary card. |
| Image placeholders for future screenshots | The PROJECT.md mentions image placeholders. Reserve space for dashboard screenshots that can be added later without layout changes. | Low | Use a styled placeholder div with a subtle pattern or icon. Aspect ratio locked to prevent layout shift when real images are added. |
| Animated step transitions on scroll | How-it-works steps animate in as user scrolls. Adds polish without requiring external dependencies. | Low | CSS `@keyframes` with `IntersectionObserver` for scroll-triggered entrance. No library needed. Degrades gracefully (content just appears without animation). |

### Design System -- Advanced

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Theme toggle (dark/light) matching silverreyes.net | Full theme toggle like the parent site, stored in localStorage, using `data-theme` attribute. Signals design maturity and consistency with the parent brand. | Medium | Requires defining complete light mode token set. The shadcn `@custom-variant dark (&:is(.dark *))` needs reworking to use `data-theme` instead. Test all components in both modes. |
| Smooth theme transition | `transition: background-color 0.2s ease, color 0.2s ease` on body/cards for smooth theme switch. silverreyes.net does this. | Low | Single CSS rule. Trivial to add, noticeable polish. |
| Branded favicon and meta tags | `<title>` and meta description matching the subdomain identity. Currently uses generic "NFL Predictor" titles. | Low | Update `index.html` head. Add Open Graph tags for social sharing. |

### Experiments Page -- Advanced

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Spread experiments alongside classifier experiments | Currently only classifier experiments are shown. Spread experiments exist in `spread_experiments.jsonl` but have no API or frontend. Showing both model types gives a complete picture. | High | Requires: new API endpoint to serve spread experiments, new TypeScript types, potentially tabbed or filtered view to separate the two experiment types. Different metric schemas (accuracy vs MAE). |
| Experiment timeline / progression view | Show experiments in chronological order with a visual timeline showing how accuracy improved over iterations. Tells the "story" of model development. | Medium | A vertical timeline with experiment dots, connected by lines. Color-coded kept/reverted. Accuracy on y-axis or as labels. Pure CSS + SVG, no charting library needed. |
| Sortable by multiple metrics | Current table sorts by experiment_id or val_accuracy_2023 only. Users may want to sort by log_loss, brier_score, or any validation year. | Low | Extend the existing sort handler to support additional SortField values. The UI patterns are already built. |
| Search/filter by hypothesis text | With only 5 classifier experiments this is unnecessary, but if experiments grow it becomes valuable. | Low | Simple text input filtering the experiments array. |
| Delta from previous best | Show "+1.68pp" or "-6.47pp" change from previous best accuracy. The data already exists in `prev_best_acc` field. | Low | Compute `val_accuracy_2023 - prev_best_acc`, format as pp delta with green/red coloring. Data is already in the ExperimentResponse type. |

---

## Anti-Features

Features to explicitly NOT build in v1.2.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full design system component library | Building a standalone Storybook-documented component library is massive scope. shadcn/ui components already work; they just need token reskinning. | Reskin existing shadcn components via CSS custom properties. Do not extract, wrap, or rebuild them. |
| Interactive data visualizations on landing page | D3/Chart.js charts on the landing page add complexity, bundle size, and distract from the simple message. The landing page should be informational, not analytical. | Use CSS-only visual elements (bars, badges, stat cards). Save charts for the Accuracy page. |
| Landing page SEO optimization | Server-side rendering, meta tag optimization, and sitemap generation are not needed for a personal project subdomain. The audience finds it through the parent site. | Set basic meta tags. Skip SSR, structured data, and sitemap. |
| Per-experiment comparison mode (side-by-side) | MLflow-style parallel comparison requires significant UI (checkbox selection, diff view, metric charts). With 5-10 experiments, just scrolling through expanded details is sufficient. | Keep the expandable detail view. Each experiment shows full context inline. If comparison is needed later, it's a v1.3+ feature. |
| Betting-framed landing page copy | "Beat the spread" or "Make smarter bets" language is explicitly out of scope per project constraints. The landing page must frame this as a prediction accuracy project, not a gambling tool. | Frame as: "Can machine learning predict NFL game outcomes?" Use accuracy metrics, not profit/loss language. |
| Custom animation library | Framer Motion or GSAP for page transitions and micro-interactions. Adds dependency weight for minimal gain on a data dashboard. | Use CSS transitions and `@keyframes`. The silverreyes.net parent site achieves all its animations with pure CSS. |
| Mobile-specific navigation redesign | The current sidebar collapses to a horizontal top nav on mobile. This works fine. Redesigning mobile nav for the landing page is a rabbit hole. | Keep the existing mobile nav pattern from Sidebar.tsx. Landing page uses the same AppLayout. |

---

## Feature Dependencies

```
Design System Token Definition (index.css)
  |
  +--> All Component Reskinning (Cards, Badges, Tables, Sidebar, etc.)
  |      |
  |      +--> Landing Page (uses reskinned components)
  |      |
  |      +--> Experiments Page Redesign (uses reskinned components)
  |      |
  |      +--> Existing Pages Visual Update (automatic via token cascade)
  |
  +--> Landing Page Route Setup (App.tsx routing change)
  |      |
  |      +--> Off-Season Default Routing (/ -> Home, /this-week -> ThisWeek)
  |      |
  |      +--> Sidebar Navigation Update (add Home link, update paths)
  |
  +--> Landing Page Content
         |
         +--> Hero Section (stat from useModelInfo hook)
         |
         +--> How-It-Works Section (static content)
         |
         +--> Explore CTAs (links to existing pages)
         |
         +--> Model Credentials (stats from API)

Experiments Page Redesign
  |
  +--> Replace Table layout with Card layout
  |      |
  |      +--> ExperimentCard component (new)
  |      |
  |      +--> ExperimentDetail component (existing, reuse)
  |
  +--> Full hypothesis display (remove truncation)
  |
  +--> Delta from previous best display (uses existing prev_best_acc data)
  |
  +--> [Optional] Spread experiments API + display (new endpoint, new types)
```

**Critical path:** Design tokens MUST be defined before any visual work begins. Everything cascades from the CSS custom property layer.

**Parallel work:** Landing page content and experiments redesign are independent once tokens are defined. They can be built simultaneously.

---

## MVP Recommendation

### Must ship (v1.2 core):

1. **Design system tokens in index.css** -- Map silverreyes.net palette, typography, and spacing tokens into the existing `@theme inline` block. This is the foundation everything else builds on.

2. **Landing page with hero, how-it-works, and explore CTAs** -- Static content with optional API-fed hero stat. This is the project's new front door and the primary deliverable visible to visitors.

3. **Route restructure** -- Move index to landing page, ThisWeekPage to `/this-week`. Update sidebar. Solves the off-season empty-state problem permanently.

4. **Accent color and border token migration** -- Replace all hardcoded `blue-400`/`blue-500`/`zinc-800` classes across components with semantic token references. This is the work that makes the dashboard feel cohesive with silverreyes.net.

5. **Experiments page: full hypothesis + card layout** -- Remove truncation, replace table with cards, keep existing ExperimentDetail content intact.

### Defer to later (nice-to-have or v1.3):

- **Theme toggle (dark/light)**: Ship dark-only for v1.2. The light mode token set needs testing across all components.
- **Spread experiments display**: Requires new API endpoint and different metric schemas. Better as its own scoped feature.
- **Experiment timeline visualization**: Polish feature. The card-based redesign is the priority.
- **Animated scroll transitions**: CSS animations can be added after content is finalized without layout changes.
- **Live hero stat from API**: Start with static numbers. Wire up API later since the hook already exists.

---

## Sources

- silverreyes.net design system analysis via WebFetch (CSS tokens, typography, card patterns, theme toggle implementation)
- Existing codebase analysis: `index.css` (current token definitions), all 31 .tsx components, experiment data schemas
- Hero section best practices: [LogRocket](https://blog.logrocket.com/ux-design/hero-section-examples-best-practices/), [Prismic](https://prismic.io/blog/website-hero-section), [Perfect Afternoon](https://www.perfectafternoon.com/2025/hero-section-design/)
- Data table UX patterns: [Pencil & Paper](https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-data-tables), [UX Patterns Dev](https://uxpatterns.dev/patterns/data-display/table)
- Empty state design: [NN/g](https://www.nngroup.com/articles/empty-state-interface-design/), [Carbon Design System](https://carbondesignsystem.com/patterns/empty-states-pattern/)
- shadcn/ui Tailwind v4 migration: [shadcn docs](https://ui.shadcn.com/docs/tailwind-v4), [Shadcnblocks](https://www.shadcnblocks.com/blog/tailwind4-shadcn-themeing/)
- Design system migration patterns: [Mercari Engineering](https://engineering.mercari.com/en/blog/entry/20221207-web-design-system-migrating-web-components-to-react/), [HashByt](https://hashbyt.com/blog/migrate-react-uis)
- ML explanation for non-technical users: [MIT Sloan](https://mitsloan.mit.edu/ideas-made-to-matter/machine-learning-explained), [IBM](https://www.ibm.com/think/topics/machine-learning-algorithms)
