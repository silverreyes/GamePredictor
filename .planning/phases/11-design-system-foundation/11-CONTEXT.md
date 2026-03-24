# Phase 11: Design System Foundation - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Migrate the dashboard's visual identity to match silverreyes.net: warm amber palette, Syne + IBM Plex Mono typography, and semantic CSS custom properties replacing all hardcoded Tailwind color classes. Dark mode only (light mode deferred to v1.3). No decorative elements (grid backgrounds, corner ticks deferred to v1.3).

</domain>

<decisions>
## Implementation Decisions

### Confidence tier visual identity
- Traffic-light color scheme: green (high), amber (medium), desaturated red (low)
- Replaces current blue-based confidence tiers
- PickCard left border uses the 3px left border pattern (existing pattern preserved), with colors swapped to green/amber/red
- ConfidenceBadge text and background also use the traffic-light colors (badge matches border color) with subtle bg tint per tier
- Consistent signal: card border and badge reinforce the same tier color

### Claude's Discretion
- Exact oklch values for the silverreyes.net palette tokens (background, card, accent, muted, border, etc.) -- verify against live site
- Syne + IBM Plex Mono font setup and weight selection
- Which heading levels use Syne vs which elements use IBM Plex Mono
- Strategy for replacing ~25 hardcoded zinc-*/blue-* Tailwind classes with semantic tokens
- shadcn/ui @theme inline block remapping approach
- Font hosting method (@fontsource or self-hosted)
- Exact green, amber, and desaturated red oklch values for confidence tiers

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design system source
- `silverreyes.net` (live site) -- Reference for exact oklch palette values, typography, and visual language. Must verify current CSS custom properties against the deployed site.

### Requirements
- `.planning/REQUIREMENTS.md` DSGN-01 through DSGN-04 -- Color palette, typography, hardcoded class replacement, shadcn/ui token remapping

### Current theme
- `frontend/src/index.css` -- Current shadcn/ui theme tokens (oklch format), @theme inline block, font imports. This is the primary file being migrated.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/index.css`: Already has oklch-based CSS custom properties with `:root` and `.dark` blocks, plus `@theme inline` block mapping shadcn tokens. Migration changes VALUES, not structure.
- 9 shadcn/ui components: badge, button, card, collapsible, select, separator, skeleton, table, tooltip
- `frontend/src/components/shared/ConfidenceBadge.tsx`: Hardcoded tier-to-class mapping (`high: "bg-blue-500/20 text-blue-400"`) -- needs traffic-light colors
- `frontend/src/components/picks/PickCard.tsx`: Hardcoded `tierBorderColors` mapping (`high: "border-blue-500"`) -- needs traffic-light colors

### Established Patterns
- Tailwind v4 with `@import "tailwindcss"` and `@import "shadcn/tailwind.css"`
- Custom variant: `@custom-variant dark (&:is(.dark *))` -- app is always in dark mode
- Font imports currently via Google Fonts CDN (Inter + JetBrains Mono)

### Integration Points
- `frontend/src/components/layout/Sidebar.tsx`: Heavy hardcoded zinc-800/blue-500 usage (borders, backgrounds, active states) -- largest single migration target
- `frontend/src/components/experiments/ExperimentDetail.tsx`: Blue-500 progress bars, zinc-800 backgrounds
- `frontend/src/components/history/HistoryLegend.tsx`: zinc-800/zinc-900 borders and backgrounds
- `frontend/src/pages/AccuracyPage.tsx` and `HistoryTable.tsx`: zinc-800 hover states

</code_context>

<specifics>
## Specific Ideas

No specific requirements -- open to standard approaches for palette mapping and font setup. User chose traffic-light confidence scheme (green/amber/red) with clear intent for intuitive signal strength.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 11-design-system-foundation*
*Context gathered: 2026-03-24*
