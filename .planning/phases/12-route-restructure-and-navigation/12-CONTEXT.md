# Phase 12: Route Restructure and Navigation - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Reorganize application routes so `/` serves the landing page in a standalone full-width layout (no sidebar), all dashboard pages live under their own routes with the sidebar layout, and navigation reflects the new structure. The actual landing page content is Phase 13 -- this phase only sets up routes, layouts, and navigation.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
User had no strong preferences on the gray areas below -- Claude has full flexibility on all implementation choices for this phase:

- **Home tab placement and icon** -- Where Home appears in the sidebar nav order, what icon to use (e.g., Home from lucide-react), label text ("Home" vs site name)
- **Sidebar branding** -- Whether to update "NFL Predictor" text to "NFL Nostradamus" or "Nostradamus" to match the landing page (Phase 13 uses "NFL Nostradamus")
- **Landing page placeholder** -- What `/` renders between Phase 12 (route setup) and Phase 13 (content). Options: minimal placeholder with site name and link into dashboard, or a simple redirect to `/this-week` until Phase 13 is built
- **Layout transition** -- How navigation between the landing page (full-width, no sidebar) and dashboard (sidebar) feels -- abrupt layout switch vs. any transition treatment
- **Route structure** -- Whether to use nested routes with two layout wrappers (one for landing, one for dashboard) or flat routes with per-route layout assignment

### Locked from Requirements
- NAV-01: Sidebar includes a Home tab linking to `/`
- NAV-02: This Week page moves from `/` to `/this-week`
- NAV-03: All existing routes (`/accuracy`, `/experiments`, `/history`) continue to work unchanged

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` NAV-01 through NAV-03 -- Home tab, This Week route move, existing route preservation

### Current routing
- `frontend/src/App.tsx` -- Current route definitions: all 4 routes nested under AppLayout, This Week at `/` index
- `frontend/src/components/layout/AppLayout.tsx` -- Dashboard layout wrapper (Sidebar + Outlet)
- `frontend/src/components/layout/Sidebar.tsx` -- Navigation items, branding, NavLink active states, mobile top nav

### Phase 13 dependency
- `.planning/ROADMAP.md` Phase 13 -- Landing page content and LAND-06 (standalone full-width layout, no sidebar). Phase 12 must create the route and layout shell that Phase 13 fills.

### Design system (Phase 11)
- `.planning/phases/11-design-system-foundation/11-CONTEXT.md` -- Semantic tokens, amber palette, Syne + IBM Plex Mono. Phase 12 nav changes should use the same token system.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AppLayout.tsx`: Clean Sidebar + Outlet pattern -- dashboard layout wrapper stays as-is, just needs routes restructured above it
- `Sidebar.tsx`: `navItems` array is a simple data structure -- adding/reordering nav items is trivial
- `Sidebar.tsx`: Already handles both desktop sidebar and mobile top nav -- both need Home tab added
- lucide-react icons already imported -- Home icon available from same package

### Established Patterns
- React Router v7 (`react-router` import) with `BrowserRouter`, `Routes`, `Route`
- Nested routes under layout component (`<Route element={<AppLayout />}>`)
- `NavLink` with `end` prop for index route, `isActive` callback for styling
- Semantic color tokens (bg-card, bg-accent, text-foreground, etc.) from Phase 11 migration

### Integration Points
- `App.tsx` route tree: Currently flat under single AppLayout -- needs split into two layout branches (landing + dashboard)
- `Sidebar.tsx` navItems array: Currently has This Week at `/` -- needs update to `/this-week` and new Home entry at `/`
- Mobile nav in Sidebar.tsx: Same navItems array drives both desktop and mobile -- single update covers both

</code_context>

<specifics>
## Specific Ideas

No specific requirements -- open to standard approaches. Phase is primarily structural (routing + nav), with the landing page content built in Phase 13.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 12-route-restructure-and-navigation*
*Context gathered: 2026-03-24*
