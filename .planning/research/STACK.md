# Technology Stack: v1.2 Design System Migration & Landing Page

**Project:** NFL Game Predictor (Nostradamus)
**Researched:** 2026-03-24
**Scope:** Additions/changes for design system alignment with silverreyes.net, landing page, experiments page redesign. Does NOT re-research existing validated stack (React 19, Vite 7, Tailwind v4, shadcn/ui 4, FastAPI, PostgreSQL, etc.).

## Current Stack Baseline

Already in `package.json` -- no changes needed to these:

| Package | Current Version | Status |
|---------|----------------|--------|
| react | ^19.2.4 | Keep |
| tailwindcss | ^4.2.1 | Keep |
| @tailwindcss/vite | ^4.2.1 | Keep |
| shadcn | ^4.0.8 | Keep |
| tw-animate-css | ^1.4.0 | Keep -- provides hero animations |
| react-router | ^7.13.1 | Keep |
| lucide-react | ^0.577.0 | Keep |
| class-variance-authority | ^0.7.1 | Keep |
| clsx / tailwind-merge | current | Keep |

## Stack Additions

### Fonts: Self-Hosted via Fontsource

| Package | Version | Purpose | Why |
|---------|---------|---------|-----|
| @fontsource/syne | latest | Display/heading font | Self-hosted woff2 files bundled by Vite. Eliminates render-blocking CDN request. Syne is the display font used on silverreyes.net -- geometric, modern, distinctive at heading sizes. |
| @fontsource/ibm-plex-mono | latest | Monospace font | Replaces JetBrains Mono for brand consistency with silverreyes.net. IBM Plex Mono has better readability at small sizes for data-heavy dashboard tables and stats. |

**Confidence: HIGH** -- Both packages verified on npm (Fontsource is the standard self-hosting approach for Vite/React, recommended by web.dev best practices).

**Why Fontsource over Bunny Fonts CDN:**
- Self-hosted fonts are bundled into the Vite build -- zero external HTTP requests at runtime
- The app is already served via Caddy on a VPS, so fonts travel the same CDN path as the app itself
- Bunny Fonts would add a render-blocking external CSS fetch, which Fontsource eliminates entirely
- Fontsource packages are tree-shakeable -- import only the weights you need
- Bunny Fonts CDN (`fonts.bunny.net`) is the right choice for static sites without a build step; this project has Vite

**Why NOT Google Fonts:**
- Currently using Google Fonts for Inter + JetBrains Mono (line 2 of `index.css`)
- This is a render-blocking external request that should be removed regardless of the design migration
- Fontsource replaces both the old fonts and adds the new ones

### No New Animation Library Needed

**tw-animate-css already provides everything needed for the landing page hero:**

| Animation Need | tw-animate-css Class | Notes |
|----------------|---------------------|-------|
| Fade in on load | `animate-in fade-in` | Combine with `duration-700` |
| Slide up from below | `animate-in slide-in-from-bottom-4` | Customize distance with `-4`, `-8`, etc. |
| Zoom in effect | `animate-in zoom-in-95` | Subtle scale from 95% to 100% |
| Staggered entrance | Manual `delay-*` classes | Apply `delay-150`, `delay-300`, `delay-500` to successive elements |
| Blur reveal | `animate-in blur-in-sm` | Available in tw-animate-css |

**Confidence: HIGH** -- Verified from tw-animate-css GitHub README. These utilities compose cleanly: `animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300`.

**Why NOT Framer Motion / Motion:**
- The hero section needs entrance animations only (fade + slide + stagger) -- CSS handles this perfectly
- Adding Framer Motion would add ~30KB to the bundle for animations that run once on page load
- No scroll-triggered animations, no drag, no layout animations, no exit animations needed
- If future milestones need complex interactive animations (drag-to-reorder, shared layout transitions), revisit then
- tw-animate-css is already installed and integrated with shadcn/ui components

### No New Packages for the Design System Migration

The design system migration is purely a CSS variable swap in `index.css`. No new packages needed because:

1. **Color palette swap** -- Replace oklch values in `:root` and `.dark` CSS variable blocks
2. **Font family swap** -- Update `@theme inline` block's `--font-sans` and `--font-mono`
3. **Custom accent color** -- Add `--color-amber-*` scale via `@theme` directive (Tailwind v4 native)
4. **Spacing/radius adjustments** -- Modify existing `--radius` value in `:root`

## Recommended Stack Changes (CSS Only, No New Deps)

### 1. Color Palette: silverreyes.net Warm Amber Theme

Replace the current neutral gray oklch palette with warm amber tones. The target colors from silverreyes.net:

| Token | Hex | OKLCH | Role |
|-------|-----|-------|------|
| Amber accent | #f0a020 | `oklch(0.767 0.157 71.7)` | Primary action color, links, active nav |
| Near-black bg | #080807 | `oklch(0.134 0.003 107)` | Dark mode background |
| Warm white | #faf5ed | `oklch(0.970 0.012 83)` | Light mode background (warm tint) |
| Warm muted | #a09080 | `oklch(0.660 0.035 65)` | Muted text, secondary content |
| Surface dark | #161614 | `oklch(0.190 0.004 100)` | Card/surface in dark mode |
| Border dark | #2a2826 | `oklch(0.260 0.006 70)` | Borders in dark mode |

**Implementation approach -- modify `index.css` only:**

```css
/* Replace current :root block */
:root {
  --background: oklch(0.970 0.012 83);     /* warm white, not pure white */
  --foreground: oklch(0.145 0.005 70);     /* near-black with warm cast */
  --primary: oklch(0.767 0.157 71.7);      /* amber accent */
  --primary-foreground: oklch(0.134 0.003 107); /* near-black on amber */
  /* ... remaining tokens follow warm palette */
}

.dark {
  --background: oklch(0.134 0.003 107);    /* near-black */
  --foreground: oklch(0.940 0.010 80);     /* warm off-white text */
  --card: oklch(0.190 0.004 100);          /* warm surface */
  --primary: oklch(0.767 0.157 71.7);      /* amber stays same */
  /* ... remaining tokens */
}
```

**Key design principle:** The current shadcn/ui setup already uses the `--background`/`--foreground` convention with oklch values. Every shadcn component (Card, Button, Badge, Table, etc.) reads from these CSS variables. Swapping the values changes the entire theme with zero component code changes.

**Confidence: HIGH** -- Verified by reading the existing `index.css` (136 lines) and the shadcn/ui v4 theming docs. The architecture is designed for exactly this kind of palette swap.

### 2. Font Integration Strategy

**Current state (index.css line 2):**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400&display=swap');
```

**Target state:**
```css
/* Remove Google Fonts import entirely */
/* Add Fontsource imports at top of index.css or in main.tsx */
```

**In main.tsx (or index.css):**
```typescript
import "@fontsource/syne/400.css";
import "@fontsource/syne/600.css";
import "@fontsource/syne/700.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
```

**In index.css `@theme inline` block:**
```css
@theme inline {
  --font-sans: 'Syne', ui-sans-serif, system-ui, -apple-system, sans-serif;
  --font-mono: 'IBM Plex Mono', ui-monospace, monospace;
  /* ... rest of theme inline remains the same */
}
```

**In `body` rule:**
```css
body {
  margin: 0;
  font-family: Syne, ui-sans-serif, system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

**Font weight mapping:**
- Syne 400 -- body text, nav items, table cells
- Syne 600 -- section headings, card titles, stat labels
- Syne 700 -- hero heading, page titles
- IBM Plex Mono 400 -- data values, experiment IDs, code snippets
- IBM Plex Mono 500 -- stat numbers, prediction percentages (for slight emphasis)

**Confidence: HIGH** -- Fontsource import pattern verified on npm docs. Syne supports weights 400-800, IBM Plex Mono supports 100-700.

### 3. Landing Page Routing (No New Deps)

The landing page sits outside the existing `AppLayout` (which has the sidebar). This is a routing change, not a stack addition:

```typescript
// App.tsx -- add a new route outside AppLayout
<Routes>
  <Route index element={<LandingPage />} />          {/* NEW: landing at / */}
  <Route element={<AppLayout />}>
    <Route path="this-week" element={<ThisWeekPage />} />  {/* moved from index */}
    <Route path="accuracy" element={<AccuracyPage />} />
    <Route path="experiments" element={<ExperimentsPage />} />
    <Route path="history" element={<HistoryPage />} />
  </Route>
</Routes>
```

No new packages needed -- `react-router` ^7.13.1 already supports this pattern.

### 4. Experiments Page Collapsible Descriptions (No New Deps)

The `collapsible.tsx` shadcn component already exists in the project (`frontend/src/components/ui/collapsible.tsx`). It uses `@base-ui/react` (already in `package.json` at ^1.3.0). This is sufficient for expandable experiment description rows.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Font loading | Fontsource (self-hosted) | Bunny Fonts CDN | Extra HTTP request, render-blocking. Fontsource bundles into Vite build. |
| Font loading | Fontsource (self-hosted) | Google Fonts CDN | Privacy concerns, render-blocking, already moving away from it. |
| Font loading | Fontsource (self-hosted) | Manual @font-face + woff2 files in /public | More maintenance, no tree-shaking, Fontsource handles subsetting. |
| Animations | tw-animate-css (already installed) | Framer Motion | 30KB bundle for one-shot entrance animations. Overkill. |
| Animations | tw-animate-css (already installed) | CSS @keyframes in index.css | Works but tw-animate-css already provides composable utilities. |
| Animations | tw-animate-css (already installed) | GSAP | Heavy (70KB+), commercial license concerns, wrong tool for simple fades. |
| Color format | oklch (native) | HSL | Tailwind v4 and shadcn/ui v4 default to oklch. More perceptually uniform. Switching to HSL would fight the framework. |
| Theme approach | CSS variable swap in :root | shadcn themes CLI | The CLI generates the same CSS variables. Direct editing is simpler for a specific palette. |
| Design tokens | CSS variables in index.css | Separate theme.css file | Single file is simpler. If a shared design system package emerges later across silverreyes.net subdomains, extract then. |

## What NOT to Add

| Package | Why Skip |
|---------|----------|
| Framer Motion / Motion | No complex animations needed. tw-animate-css covers entrance effects. |
| @tailwindcss/typography | No prose/article content on the landing page. Stats and CTAs only. |
| Any icon library beyond Lucide | Lucide already covers all needed icons. |
| Recharts / D3 | No new charts needed for landing page or experiments redesign. |
| Any state management (Zustand, Jotai) | TanStack Query handles server state. Landing page is static content. |
| CSS-in-JS (styled-components, Emotion) | Already committed to Tailwind utility classes. |
| next-themes or similar | The app is dark-mode only in practice (dark sidebar, dark cards). If light mode is needed later, the `:root`/`.dark` CSS variables already support it. |

## Installation

```bash
cd frontend

# Only two new packages needed
npm install @fontsource/syne @fontsource/ibm-plex-mono
```

That is the entire list of new dependencies. Everything else is CSS variable modifications in `index.css`.

## Integration Checklist

1. **Remove** Google Fonts `@import` from `index.css` line 2
2. **Add** Fontsource imports in `main.tsx` (or `index.css`)
3. **Update** `:root` CSS variables with warm amber oklch palette
4. **Update** `.dark` CSS variables with near-black amber palette
5. **Update** `@theme inline` block: `--font-sans` to Syne, `--font-mono` to IBM Plex Mono
6. **Update** `body` font-family rule
7. **Replace** hardcoded Tailwind color classes in Sidebar (`bg-zinc-900`, `border-zinc-800`, `bg-blue-500/10`, `text-blue-400`) with semantic tokens (`bg-card`, `border-border`, `bg-primary/10`, `text-primary`)
8. **Add** landing page route outside AppLayout wrapper
9. **Build** landing page using existing shadcn components (Card, Button, Badge) + tw-animate-css entrance animations
10. **Refactor** ExperimentsPage to use existing Collapsible component for expandable descriptions

## Hardcoded Color Audit

The Sidebar component has hardcoded Tailwind colors that bypass the theme system and MUST be migrated to semantic tokens:

| Current Class | Replacement | Location |
|---------------|-------------|----------|
| `bg-zinc-900` | `bg-card` or `bg-sidebar` | Sidebar background |
| `border-zinc-800` | `border-border` or `border-sidebar-border` | Sidebar border, separator |
| `bg-blue-500/10` | `bg-primary/10` | Active nav item background |
| `text-blue-400` | `text-primary` | Active nav item text |
| `hover:bg-zinc-800` | `hover:bg-muted` | Nav item hover |
| `bg-zinc-900/50` | `bg-muted/50` | ModelStatusBar card |

Other components likely have similar hardcoded colors. A full grep for `zinc-`, `blue-`, `gray-`, `slate-` in `.tsx` files should be done during implementation.

## OKLCH Color Conversion Reference

For implementation, here are the computed oklch values for the silverreyes.net palette:

```css
/* Primary palette */
--amber-accent:     oklch(0.767 0.157 71.7);   /* #f0a020 */
--near-black:       oklch(0.134 0.003 107);     /* #080807 */

/* Derived tokens (adjust lightness for semantic roles) */
--amber-50:         oklch(0.970 0.025 80);      /* very light amber tint */
--amber-100:        oklch(0.930 0.040 78);      /* light amber */
--amber-200:        oklch(0.870 0.070 76);      /* medium-light amber */
--amber-500:        oklch(0.767 0.157 71.7);    /* primary amber */
--amber-600:        oklch(0.680 0.145 70);      /* darker amber for hover */
--amber-700:        oklch(0.590 0.130 68);      /* dark amber */
--amber-900:        oklch(0.350 0.070 65);      /* very dark amber */

/* Warm neutrals (hue ~70-80 instead of pure gray hue 0) */
--warm-50:          oklch(0.970 0.012 83);      /* warm white background */
--warm-100:         oklch(0.940 0.010 80);      /* warm off-white */
--warm-200:         oklch(0.880 0.010 75);      /* warm light gray */
--warm-400:         oklch(0.660 0.035 65);      /* warm muted text */
--warm-600:         oklch(0.450 0.020 70);      /* warm dark gray */
--warm-800:         oklch(0.260 0.006 70);      /* warm border dark */
--warm-900:         oklch(0.190 0.004 100);     /* warm surface dark */
--warm-950:         oklch(0.134 0.003 107);     /* near-black */
```

## Sources

- [shadcn/ui Theming Docs](https://ui.shadcn.com/docs/theming) -- CSS variable structure, oklch format (HIGH confidence)
- [shadcn/ui Tailwind v4 Migration](https://ui.shadcn.com/docs/tailwind-v4) -- `@theme inline` pattern, `.dark` selector approach (HIGH confidence)
- [Tailwind CSS v4 Theme Variables](https://tailwindcss.com/docs/theme) -- `@theme` directive syntax, namespace conventions, keyframes (HIGH confidence)
- [tw-animate-css GitHub](https://github.com/Wombosvideo/tw-animate-css) -- Available animation utilities, composable classes (HIGH confidence)
- [@fontsource/syne on npm](https://www.npmjs.com/package/@fontsource/syne) -- Self-hosted Syne font, weights 400-800 (HIGH confidence)
- [@fontsource/ibm-plex-mono on npm](https://www.npmjs.com/package/@fontsource/ibm-plex-mono) -- Self-hosted IBM Plex Mono, weights 100-700 (HIGH confidence)
- [Bunny Fonts - Syne](https://fonts.bunny.net/family/syne) -- Font availability, weights confirmed (MEDIUM confidence -- used for verification only)
- [Bunny Fonts - IBM Plex Mono](https://fonts.bunny.net/family/ibm-plex-mono) -- Font availability confirmed (MEDIUM confidence -- used for verification only)
- [web.dev Font Best Practices](https://web.dev/articles/font-best-practices) -- Self-hosting recommendation for performance (HIGH confidence)
- [Tailwind CSS v4 Theming Discussion](https://github.com/tailwindlabs/tailwindcss/discussions/18471) -- Community patterns for multi-theme v4 (MEDIUM confidence)
- silverreyes.net -- Direct inspection of CSS variable structure, token naming conventions (HIGH confidence)
- Existing `frontend/src/index.css` -- Current theme variable structure, 136 lines (HIGH confidence -- direct file read)
- Existing `frontend/package.json` -- Current dependency versions (HIGH confidence -- direct file read)
