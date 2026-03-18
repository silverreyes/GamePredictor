# Milestones

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

