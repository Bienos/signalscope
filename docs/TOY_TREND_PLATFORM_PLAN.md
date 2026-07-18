# SignalScope Toy Trend Platform Plan

Status: implemented MVP record for `feature/toy-trend-platform`; remaining boundaries are called out below  
Scope: TikTok evidence for children's toys, family toy purchasing, and adult toy collecting only  
Operating mode at implementation: synthetic demo data; live Apify collection disabled by default

## 1. Product decision

SignalScope will be a toy-market decision system, not a generic TikTok analytics dashboard. Its daily job is to answer:

> What is gaining momentum in toys, why is it moving, how reliable is the evidence, and what original content should the team test next?

The primary user is a strategist at a mid-sized UK or European social, creative, or influencer agency serving toy brands and retailers. Secondary users are toy-brand, retailer, category, influencer, and consumer-insight teams. The product must move a user through one short workflow:

1. Review what changed.
2. Inspect an explainable toy signal.
3. Choose Act, Monitor, or Avoid.
4. Save an opportunity and add an analyst note.
5. Create a source-linked original brief with unchecked safety and originality confirmations.
6. Add reviewed opportunities to a decision-led report.

The supplied research supports the decision workflow, visible evidence, a populated first session, category watchlists, and client-ready reporting. The demand assessment also says the commercial proposition is not yet validated as broad self-service SaaS. Therefore this implementation proves the workflow with honest demo data and a controlled provider adapter; it does not claim licensed coverage, live monitoring, billing, alerts, collaboration, or complete TikTok access.

## 2. Current architecture

### Application

- Next.js 16 application with public marketing pages and an authenticated-style demo workspace.
- FastAPI modular monolith with SQLAlchemy, Alembic, JWT authentication, PostgreSQL in Docker, and SQLite support for tests.
- Provider boundary with mock, CSV/JSON import, generic REST, and a disabled Apify proof of concept.
- Append-only video snapshots, per-video scoring, daily reports, and CSV/XLSX/HTML exports.

### Reusable foundations

- Backend provider protocol, factory, imports, mock data, auth dependencies, snapshot ingestion, and export services.
- Frontend app shell, locale support, loading/error states, data-health surface, feature gates, responsive breakpoints, and reduced-motion support.

## 3. Baseline defects addressed and remaining debt

The data, product and provider defects below describe the baseline that motivated this branch. The
toy-specific APIs, nullable ingestion, provider package, signal workflow and frontend now address the
listed core defects. Remaining material debt is: a shared seeded browser identity, read-only/non-user-
filtered stored watchlists, no background scheduler or alerts, no production billing/collaboration,
no fully automated data-quality circuit breaker, and unverified commercial provider rights.

### Addressed in the MVP

- Collection market, account region and audience geography are separated.
- Missing metrics remain nullable; two observations are required for velocity and three for acceleration.
- Provider/mode identity, provenance, run accounting, pagination, structured errors, quarantine and
  bounded costs are implemented without exposing provider field names outside the adapter.
- First-class toy signals, persistent per-user decisions/opportunities, guarded briefs and
  decision-led reports replace post-only navigation.
- The product navigation, central toy fixtures, brand tokens, responsive behavior and typed frontend
  contracts are implemented.
- Mocked provider tests cover the integration without paid Actor calls.

### Still open

- Browser login and owner-scoped records are implemented; production identity, tenancy, SSO and client workspaces are absent.
- Stored toy watchlists are read-only and their read route is not user-filtered.
- Monitoring produces read-only, provider-mode-isolated schedules/plans only. Due planning is capped
  by the configured provider URL limit and a hard maximum of 20 canonical URLs, and groups preflights by market; no scheduler, queue, automatic refresh or
  alert delivery is connected.
- Some quality stop conditions remain analyst-visible guidance rather than a universal circuit breaker.
- Billing, collaboration, commercial provider rights and production security/retention operations
  are not complete.
- Historical migration `0001` still depends on current ORM metadata and must not be edited.

## 4. Scope decisions

### Must implement now

- Toy-only EN/PL taxonomy and seeds.
- Provider-independent nullable contracts and explicit provenance.
- Safe Apify input builders, dry-run preflight, async start/poll/dataset client, pagination, redaction, budget limits, run records, and synthetic tests.
- Immutable snapshots linked to provider runs.
- Toy signal clustering, lifecycle, opportunity score, confidence, saturation, and evidence explanation.
- Persistent decisions, analyst notes, opportunities, and source-linked creative briefs.
- `/api/toys/*` resources and admin-only provider execution routes.
- Today, Discover, Signal Detail, Track, Opportunities, Reports, and Workspace user paths.
- Decision-first reporting and secondary raw exports.
- Approved brand tokens, logo assets, responsive behavior, accessibility corrections, and explicit `DEMO TOY DATA` / live-provider labels.

### Prototype only

- Per-browser JWT session; decisions, opportunities and reports are keyed to the authenticated
  backend user, while stored watchlists remain seeded/read-only and are not safely tenant-filtered.
- Manual report review and inclusion workflow.
- Deterministic toy classification and clustering; every classification remains reviewable.
- Provider cost estimate based on a configurable unit-cost assumption.

### Post-MVP

- Scheduled alerts, assignments, comments, multi-client workspaces, white labelling, SSO, data warehouse export, custom scoring, historical replay, and a second contracted provider.
- Optional profile enrichment after a creator qualifies and after provider economics are validated.
- A managed-service operating layer for weekly analyst review and outcome tracking.

### Do not build yet

- Publishing, creator payments, influencer CRM, TikTok Shop, comments, transcripts, followers/following identities, audience inference, child-creator classification, media download, virality prediction, or broad non-toy verticals.
- Production billing or enforcement without a real billing integration.
- Claims of exhaustive, real-time, licensed, or official TikTok coverage.

## 5. Final information architecture

### Primary navigation

1. **Today** — `/dashboard`
2. **Discover** — `/discover`
3. **Track** — `/track`
4. **Opportunities** — `/opportunities`
5. **Reports** — `/reports`
6. **Workspace** — `/workspace`

### Secondary routes

- Signal detail: `/signals/[id]`
- Track tabs: `/track?tab=watchlists|creators|hashtags|sounds`
- Workspace pages: `/data-health`, `/settings`, `/pricing`, and public methodology/legal routes.
- Existing `/watchlists`, `/creators`, `/hashtags`, `/sounds`, `/ideas`, and `/review-queue` remain redirects or compatibility views.

### Reading order

1. Is the dataset usable?
2. What changed?
3. What needs a decision?
4. What evidence and limitation explain the recommendation?
5. What original action should be tested?
6. What belongs in the next report?

## 6. Backend provider architecture

The Apify implementation is bounded inside `backend/app/providers/apify/`:

- `client.py` — maintained synchronous Apify Python client wrapper, paginated dataset iteration, configured retries/timeouts, token redaction, and structured errors.
- `inputs.py` — typed API Dojo and Clockworks keyword, hashtag, approved-profile, and direct-video builders with provider-specific safety assertions.
- `schemas.py` — API Dojo, Clockworks and run schemas. Provider-specific raw keys exist only here and in the normalizer.
- `normalizer.py` — raw Actor result to provider-independent records; invalid rows become quarantined records instead of failing the complete dataset.
- `costs.py` — maximum-result and configurable maximum-cost preflight plus monthly-budget checks.
- `capabilities.py` — honest enabled/disabled capability contract.
- `errors.py` — authentication, rate limit, timeout, invalid response, partial result, budget, and disabled-provider errors.
- `provider.py` — integration with the existing provider boundary.

The primary Actor is `apidojo/tiktok-scraper-api`. `clockworks/tiktok-scraper` is an automatic fallback only after retryable primary failures. Optional hashtag-led expansion uses `clockworks/tiktok-discover-scraper` and is disabled by default. No Actor is called during tests or CI.

## 7. Normalized data contracts

### Provider collection context

- provider and Actor identifiers
- collection type: keyword, hashtag, approved profile, or direct refresh
- collection market and language context
- query provenance
- external run and dataset identifiers
- start/finish timestamps, status, result counts, schema fingerprint, cost, and redacted error state

### Creator

- provider identity, username, display name, profile URL
- provider-supplied account region, explicitly not audience geography
- nullable followers and verified state
- creator type, last observed time, and provenance

### Video

- provider identity and canonical evidence link
- nullable publication time
- caption, provider language, detected language, collection market
- toy category, content mechanism, safety flags, availability
- discovery query, first/last observed timestamps, provider provenance, and missing fields
- no downloaded media

### Snapshot

- immutable collection time and provider freshness
- nullable views, likes, comments, shares, saves, and creator followers
- availability, provider run, source, and missing fields

### Toy signal

- title, category, mechanism, lifecycle, recommendation, confidence, score version
- post/creator counts, markets, languages, hashtags, sounds, saturation
- main supporting evidence, contradictory evidence, missing components, safety state, and explanation
- links to representative video evidence

### Decision and opportunity

- persistent Act/Monitor/Avoid state, reason, note, and review date
- saved opportunity linked to exactly one source signal
- creative brief with original hook, structure, creator type, production complexity, decision window, non-copy guidance, safety, rights, and evidence limitations
- originality and safety confirmations start false

## 8. Database migrations

- `0005_toy_trend_foundations` follows `0004_apify_provider_evidence`. It expands provider evidence,
  makes acceleration nullable, and adds toy signals, evidence memberships, decisions,
  opportunities/briefs, watchlists and quarantine records.
- `0006_user_scoped_reports` follows `0005`. It adds non-null `daily_reports.user_key`, backfills
  existing rows with `single-user`, replaces the date-only uniqueness rule with
  `(report_date, user_key)`, and adds report-date/user indexes.

Report list, detail, review and export routes now filter by the authenticated user's key. The local
browser still uses one seeded demo identity, so this is report ownership enforcement, not a complete
multi-tenant identity system. Fresh SQLite, upgraded SQLite and PostgreSQL must all reach `0006` via
`alembic upgrade head`; historical migrations must not be edited.

## 9. Toy taxonomy

`backend/app/domain/toys/seeds.json` is the canonical JSON seed file for English and Polish discovery terms, hashtags, product-category phrases, content mechanisms, creator types, and safety flags. It includes the categories and mechanisms in the implementation brief and treats all search terms as discovery seeds, never verified trends. Environment variables are explicit run overrides; frontend fallback fixtures are not an authoritative taxonomy.

Classification is deterministic, reviewable, versioned, and conservative:

- no creator age inference
- no child identity inference
- no audience-age or audience-geography inference
- popularity and safety remain separate
- uncertain category, creator type, rights, or safety values remain `Unknown` or `Review`

## 10. Trend methodology

### Per-video observations

- Velocity requires two snapshots containing views and a positive elapsed interval.
- Acceleration requires three such snapshots and is otherwise null.
- Metric decreases are recorded as contradictory/anomaly evidence, not labelled fraud.
- Creator baseline is used only after enough comparable recent posts exist; otherwise the component is missing.

### Signal clustering

The first version uses an explainable cluster key based on collection market, toy category, and content mechanism, then adds supporting hashtag, sound, and caption-pattern overlap. It does not use black-box similarity as observed fact. Representative videos retain canonical source links.

### Signal lifecycle

- `Insufficient evidence`: fewer than two usable observations or inadequate creator spread.
- `Emerging`: early positive evidence across a small independent set.
- `Accelerating`: interval velocity and independent adoption are increasing.
- `Breakout`: strong multi-creator acceleration with a still-open opportunity window.
- `Viral`: high distribution and broad observed adoption.
- `Saturated`: broad adoption with low differentiation or flattening acceleration.
- `Declining`: momentum has passed its recent peak.
- `Recurring`: a previously active pattern receives a new observation after at least 72 hours and
  shows positive re-acceleration; continuous-window repetition is not enough.

One observation always produces `Insufficient evidence`.

### Opportunity score

Versioned components include post velocity, acceleration, unique-creator growth/diversity, toy relevance, observed shares/saves, freshness, saturation penalty, and evidence completeness. Missing components remain listed and reweighting is explicit. The output is an opportunity score, not a virality prediction.

### Confidence

Confidence uses snapshot count, independent creators, field completeness, freshness, cohort size, market consistency, contradictory evidence, and provider health. It is not derived from score magnitude. Single-market evidence explicitly lacks cross-market confirmation and must not imply geographic spread.

## 11. API design

### Read resources

- `GET /api/toys/overview`
- `GET /api/toys/signals`
- `GET /api/toys/signals/{signal_id}`
- `GET /api/toys/videos`
- `GET /api/toys/creators`
- `GET /api/toys/hashtags`
- `GET /api/toys/sounds`
- `GET /api/toys/watchlists`
- `GET /api/toys/opportunities`
- `GET /api/toys/reports`
- `GET /api/toys/data-health`

### Decision workflow

- `POST /api/toys/signals/{signal_id}/decision`
- `POST /api/toys/signals/{signal_id}/notes`
- `POST /api/toys/signals/{signal_id}/save`
- `POST /api/toys/signals/{signal_id}/create-brief`
- `POST /api/toys/reports`

### Admin provider operations

- `POST /api/providers/apify/preflight`
- `POST /api/providers/apify/discover`
- `POST /api/providers/apify/refresh`
- `GET /api/providers/apify/runs`
- `GET /api/providers/apify/health`
- `GET /api/providers/apify/costs`

Execution requires an administrator, enabled live mode, a token, an explicit confirmation, a bounded result count, and a passed budget preflight.

## 12. Demo and live modes

### Demo

- deterministic central fixtures only
- 12–20 toy signals, 30–50 videos, 12–20 creators, at least 20 hashtags, eight sounds, repeated observations, GB/PL and EN/PL
- all lifecycle, decision, safety, and confidence states represented
- every workspace screen visibly says `DEMO TOY DATA`

### Live provider

- disabled unless `APIFY_ENABLED=true` and `TOY_PROVIDER_MODE=live`
- no automatic call during startup, health checks, tests, or configuration checks
- preflight exposes the exact Actor payload, maximum result count, configurable maximum-cost estimate, disabled media/comment/follower controls, and token-safety confirmation
- provider responses are described as a configured monitored sample, never complete TikTok coverage
- demo configuration never exposes stored provider evidence; live configuration selects matching
  provider evidence when present and may otherwise show only an explicitly labelled demo fallback
- signal identities and report opportunities remain isolated by evidence provider/mode

## 13. Privacy, retention, and commercial rules

- Store only public identifiers, captions where permitted, source links, metadata, and metric observations required for the workflow.
- Do not store downloaded video, audio, covers, avatars, slideshows, transcripts, comments, follower identities, or following identities.
- Keep account region separate from audience geography and never infer creator or audience age.
- Keep raw payloads out of product tables; retain only a redacted/quarantined reference and schema fingerprint for the configured short retention window.
- Support deletion/tombstoning and provider unavailability states.
- Before commercial launch, obtain written rights for customer-facing analytics, repeated storage, derived metrics, identifiers, captions/links, exports, UK/EEA processing, and retention.
- Apify is not an official TikTok API; TikTok and ByteDance do not sponsor or endorse SignalScope.

## 14. Test strategy

### Backend

- safe inputs and forced-off collection features
- disabled/missing-token behavior and token redaction
- start/poll/pagination, rate limits, timeouts, auth failures, partial datasets, invalid rows, and schema changes using mock transports only
- missing values, stable deduplication, immutable/idempotent snapshots, provenance, market semantics, unavailable/deleted/private content
- velocity, acceleration, baseline minimums, lifecycle, saturation, confidence, and cost gates
- persistent decisions, notes, source-linked opportunities/briefs, and report selection
- route authorization and response contracts

### Frontend

- typed nullable contracts and formatters
- navigation, filters, lifecycle tabs, missing metrics, demo/live labels, empty/loading/error states
- decision and report flow
- mobile cards, keyboard navigation, dialogs, and visible safety/freshness
- lint, TypeScript validation, production build, and browser checks at 1440, 1024, 768, and 390 pixels

### Migration and integration

- fresh database upgrade to head
- upgrade from current `0004` state
- mocked Actor success, empty pages, multiple pages, rate limit, invalid record, auth failure, timeout, partial success, private/deleted post, and schema drift
- no paid Apify run in CI

## 15. Acceptance criteria

The implementation is accepted when:

- all product routes and copy are toy-market specific
- Apify remains disabled by default and no secret reaches frontend code or logs
- primary discovery and direct-video refresh use the one broad Actor with safe inputs
- optional profile enrichment is separately flagged off
- raw Actor names do not leave the adapter package
- unavailable metrics remain null from provider through database, API, UI, reports, and exports
- snapshots are immutable and linked to provenance
- velocity needs two observations and acceleration needs three
- lifecycle, opportunity score, confidence, saturation, and limitations are explainable
- hashtags and sounds use observed creator spread and momentum rather than accumulated volume alone
- decisions, notes, opportunities, and briefs persist and retain their source signal
- reports lead with reviewed decisions and treat raw exports as secondary
- demo/live state, mobile usability, and accessibility are testable and explicit
- mock and import providers continue to work
- backend and frontend validation commands pass
- reports are scoped to the authenticated owner and contain only explicitly selected opportunities
  from the active evidence mode
- refresh offsets and due plans exclude demo/mixed evidence, are bounded by the provider URL limit
  and a hard maximum of 20 URLs, and never schedule or start a provider run without an
  administrator's exact confirmation

## 16. Implementation order used

1. Add normalized contracts, taxonomy/seeds, nullable formatters, and the new migration.
2. Refactor the Apify adapter into a safe package and add mocked provider tests.
3. Make ingestion run-aware and correct missing-value, market, baseline, spread, and provider-status defects.
4. Build toy signal calculation, persistence, lifecycle, confidence, saturation, and evidence membership.
5. Add resource-specific toy APIs, persistent decision/opportunity/report workflows, admin preflight, and CLI commands.
6. Replace generic demo fixtures with central toy-only fixtures and seed all required states.
7. Apply the approved brand system and new information architecture.
8. Implement Today, Discover, Signal Detail, Track, Opportunities, Reports, and Workspace.
9. Add frontend contract tests and complete responsive/accessibility behavior.
10. Run migrations, backend tests/lint/types, frontend tests/lint/types/build, and browser verification.
11. Document the exact first controlled live test without executing it.
