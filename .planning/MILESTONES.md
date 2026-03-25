# Milestones

## v1.2 Design & Landing Page (Shipped: 2026-03-25)

**Phases:** 4 | **Plans:** 5 | **Files changed:** 59 | **LOC:** +7,530 / -1,294
**Timeline:** 1 day (2026-03-24)
**Git range:** feat(11-01) → feat(14-01)

**Delivered:** Unified dashboard visual identity with silverreyes.net design system, added a landing page as the public-facing front door, and fixed the experiments table for readability.

**Key accomplishments:**
1. Migrated entire dashboard to silverreyes.net visual identity — amber palette (#f0a020 accent, near-black background), Syne + IBM Plex Mono self-hosted fonts, semantic color tokens
2. Replaced all ~36 hardcoded Tailwind color classes across 14 components with semantic theme tokens (tier-high/medium/low, status-success/error/warning)
3. Restructured routes into two layout branches — LandingLayout (full-width, no sidebar) at `/` and AppLayout (sidebar) for dashboard routes
4. Built complete landing page with hero section, how-it-works explainer, explore CTAs, and footer with silverreyes.net branding
5. Fixed experiment table column alignment by removing invalid Collapsible `<div>` wrappers and enabled full hypothesis text display with natural wrapping

### Known Gaps (Deferred to v1.3)
- EXPR-03: Hybrid summary+detail layout for experiments
- EXPR-04: Visual distinction for kept vs reverted experiments beyond badge

---

## v1.1 Point Spread Model (Shipped: 2026-03-24)

**Phases:** 4 | **Plans:** 10 | **Files changed:** 58 | **LOC added:** ~7,000
**Timeline:** 2 days (2026-03-22 → 2026-03-24)
**Git range:** feat(07-01) → fix: swap Pick-Em card

**Delivered:** Ridge regression spread model predicting point margins, integrated across API, dashboard, and weekly pipeline with sportsbook-convention display.

**Key accomplishments:**
1. Ridge regression spread model (MAE 10.68, 60.2% derived winner accuracy) trained with 5-experiment sweep, production artifact saved alongside classifier
2. Spread predictions table, API endpoint `/api/spreads/{season}/{week}`, and model info/reload integration
3. Dashboard showing spread predictions on PickCards with color-coded error (green/amber/red) and sportsbook sign convention
4. Accuracy page with season selector, Pick-Em vs Spread comparison, info tooltips, and season+lifetime spread stats
5. History page legend explaining all columns, team-labeled spreads ("MIA -2.3 → BUF by 9")
6. Weekly pipeline auto-generates spread predictions (non-fatal step 5) with historical seed script for backfill

### Known Tech Debt
- Postgres integration test (`test_pbp_upsert_idempotent`) requires live DB connection, skipped in CI
- 2021/2022 stale entries in predictions table from training validation (harmless, visible in season dropdown)

---

## v1.0 MVP (Shipped: 2026-03-18)

**Phases:** 6 | **Plans:** 14 | **Commits:** 126 | **LOC:** ~8,200 (Python + TypeScript + SQL)
**Timeline:** 3 days (2026-03-15 → 2026-03-18)
**Git range:** feat(01-01) → feat(06-02)

**Delivered:** End-to-end NFL game prediction system — from raw play-by-play data to a deployed dashboard with automated weekly refresh.

**Key accomplishments:**
1. Ingested 20 seasons (2005-2024) of NFL data into PostgreSQL with normalized team abbreviations and automated validation
2. Built leakage-safe game-level features with shift(1) rolling windows, gated by 6 automated leakage tests
3. XGBoost classifier achieving 62.89% on 2023 validation — beating always-home (55.51%) and better-record (58.20%) baselines via 5-experiment autoresearch loop
4. FastAPI serving predictions, model metadata, and experiment data with token-protected hot-reload
5. React dashboard with 4 views: weekly picks, season accuracy, experiment scoreboard, prediction history
6. Docker Compose (5 services) with automated weekly refresh pipeline and human approval gate

### Known Tech Debt
- `SITUATIONAL_FEATURES` in `features/definitions.py` lists stale column names (never imported at runtime)
- `CORS_ORIGINS` in `api/config.py` hardcoded to localhost (does not affect Caddy-proxied production)
- First-run model seeding not documented (API degrades gracefully to 503)

---

