# Delivery plan

- [x] M1 repository, Docker, database, migration, seed, authentication
- [x] M2 provider abstraction, mock/CSV/JSON/generic REST, normalisation, dedupe, snapshots
- [x] M3 metrics, percentiles, scores, confidence, quality checks
- [x] M4 classification, safety rules, clustering, optional AI boundary
- [x] M5 responsive dashboard and filtered resource pages
- [x] M6 daily report, original concepts, HTML/CSV export, local/SMTP email
- [x] M7 deletion/retention, structured logs, tests, CI, deployment docs
- [x] P0 demo evidence labels, shared emerging eligibility, safety gating, report versioning
- [x] P1 auditable AVS/EVS/NPS components, cohort metadata, stronger confidence
- [x] P1 honest insufficient-history states for sounds and hashtags
- [x] P1 specialised post-table evidence, provider freshness, read-only settings disclosure
- [x] Demo creator baselines using comparable observed posts (licensed history still required for production)
- [x] Simulated seven-day hashtag and sound histories (provider observations still required for production)
- [x] Interactive local demo settings and saved views (server-side controls remain provider-dependent)
- [x] Demo provider capability registry for optional commerce/audience/rights fields
- [x] Provisional Free, Pro, Team and Enterprise packaging with 1/5/20 category-watchlist limits and optional hashtag/sound depth add-ons
- [x] Commercial UX preview with quotas, contextual upgrade states and pricing disclosure
- [x] Formats removed from primary navigation and retained as supporting creative-mechanism metadata
- [ ] Licensed provider with explicit customer-facing display, storage, export and redistribution rights
- [ ] Backend-owned workspaces, subscriptions, usage metering and server-enforced entitlements
- [ ] Billing, persistent collaboration, automated alerts and scheduled report delivery

Assumptions: this is a single-tenant internal MVP; provider metrics are licensed for internal analysis; creator region is not audience geography; official TikTok links are permitted. Missing information: licensed vendor contract, field definitions, quotas, freshness SLA, redistribution terms and credentials. Decisions: modular monolith, immutable snapshots, deterministic fallback intelligence, no stored media, JWT bearer auth, scheduled command process. Current creator baselines are demo-relative within the monitored sample and must be replaced with licensed comparable-post history before production decisions.
