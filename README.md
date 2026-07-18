# SignalScope

SignalScope is an evidence-led TikTok toy trend decision workspace for UK and European agency and consumer-brand teams. It converts a configured, non-exhaustive sample into explainable toy signals, then helps an analyst decide **Act**, **Monitor** or **Avoid**, create an original brief and prepare a client-ready report.

Current scope is deliberately narrow: children’s toys, educational/STEM and sensory toys, collectibles, construction toys, plush, dolls/action figures, outdoor toys, board games, parent/gift-buyer content and adult toy-collecting culture. It does not claim complete TikTok coverage or predict virality. SignalScope is independent and is not affiliated with TikTok or ByteDance.

## Start the demo

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.cli seed
```

Open [http://localhost:3000](http://localhost:3000). The local seed login is `admin@viralradar.local` / `RadarDemo!2026`.

The labelled demo fixture contains 48 toy videos, 20 creators, 20 hashtags, eight sounds and four immutable observations per video across GB/en and PL/pl. Its 12 explainable signals exercise Insufficient evidence, Emerging, Accelerating, Breakout, Viral, Saturated and Declining states. It never contacts TikTok.

### Demo session boundary

Local Compose explicitly sets `SIGNALSCOPE_DEMO_MODE=true`, so unauthenticated reads may use clearly labelled synthetic fixtures. The frontend never silently signs a visitor in as the demo administrator. Persistent decisions, notes, briefs, reports and exports require the browser login at `/login`, which stores the backend's short-lived JWT in an HTTP-only, same-site cookie. The seeded account is for local evaluation only; it is not tenancy, SSO or a production identity configuration. Provider-operation routes are not proxied by the browser endpoint and still require direct administrator authorization.

Migration head is `0006_user_scoped_reports`. It adds `daily_reports.user_key` and permits one report per date per authenticated user. Report list, detail, review and export endpoints enforce that owner key, but the demo browser still acts as the one seeded user.

## Daily toy workflow

```bash
# Recalculate explainable per-video evidence and toy signals
docker compose exec api python -m app.cli toy-score

# Create/update the decisions-first JSON report
docker compose exec api python -m app.cli toy-report

# Inspect provider state and recorded spend without starting a provider job
docker compose exec api python -m app.cli provider-health
docker compose exec api python -m app.cli provider-costs
```

Legacy `seed`, `collect`, `score` and `report` commands remain available. When `PROVIDER_TYPE=apify`, legacy `collect` is intentionally preflight-only and directs the operator to the guarded toy commands below.

## Apify connector (disabled by default)

The backend-only connector uses `apidojo/tiktok-scraper-api` as its primary bounded toy-data Actor. `clockworks/tiktok-scraper` is called only after a retryable primary failure; optional Clockworks Discover expansion is disabled by default. SignalScope never persists videos, covers, audio, avatars, subtitles or follower/following lists.

Keep `APIFY_TOKEN` only in `.env` or a deployment secret manager. Never use a `NEXT_PUBLIC_` variable for it and never commit the real token.

```bash
# Configuration-only check: no network call and no paid Actor run
docker compose exec api python -m app.cli apify-config-check

# Print actor inputs, safety assertions, result bounds and estimated ceiling only
docker compose exec api python -m app.cli toy-discover

# Direct URL refresh also defaults to preflight
docker compose exec api python -m app.cli toy-refresh \
  --url https://www.tiktok.com/@creator/video/1234567890123456789

# Read-only due plan plus grouped preflights; no provider run without the exact
# confirmation flag. The requested limit is clamped to both the configured
# per-request provider limit and a hard maximum of 20.
docker compose exec api python -m app.cli toy-refresh --due --limit 5
```

`toy-discover` uses the complete central taxonomy when query and hashtag overrides are blank, so it is useful for review but is not the recommended first paid test. The exact one-keyword, five-result, no-paid-default procedure is in [docs/TOY_LIVE_TEST_PLAN.md](docs/TOY_LIVE_TEST_PLAN.md). Stop after its preflight phase unless an authorised operator has approved provider rights, the displayed scope and the enforced `maxTotalChargeUsd` ceiling. No confirmation flag is implied.

See [docs/APIFY_TOY_PROVIDER.md](docs/APIFY_TOY_PROVIDER.md), [docs/TOY_FIELD_MAPPING.md](docs/TOY_FIELD_MAPPING.md), [docs/TOY_LIVE_TEST_PLAN.md](docs/TOY_LIVE_TEST_PLAN.md) and [docs/TOY_DATA_QUALITY.md](docs/TOY_DATA_QUALITY.md). Written provider permission for customer-facing display, storage, history, export and redistribution is still a commercial launch requirement.

## Architecture

```text
Next.js decision workspace
        ↓ authenticated API
FastAPI modular monolith
        ↓
PostgreSQL: provider runs → videos → immutable snapshots → toy signals
        ↓
decisions → opportunities/original briefs → reports
```

Provider field names stop at the Apify adapter. Normalised domain models preserve collection market, provider language, account region (never audience geography), missing fields, schema fingerprints and run provenance. Missing engagement values remain `null`; velocity requires two observed view values and acceleration requires three.

Evidence modes are isolated at read time and in signal identities. Demo mode never exposes stored provider evidence. Live mode selects provider evidence when it exists; if it does not, the UI may fall back only to an explicitly labelled demo state. Reports include only the authenticated user's explicitly selected opportunities from the currently selected evidence mode.

Key implementation notes are in [docs/TOY_TREND_PLATFORM_PLAN.md](docs/TOY_TREND_PLATFORM_PLAN.md), [docs/TOY_TREND_METHODOLOGY.md](docs/TOY_TREND_METHODOLOGY.md), [docs/TOY_API_CONTRACTS.md](docs/TOY_API_CONTRACTS.md), [docs/TOY_FRONTEND.md](docs/TOY_FRONTEND.md) and [docs/TOY_PRIVACY_AND_RETENTION.md](docs/TOY_PRIVACY_AND_RETENTION.md).

## Verification

```bash
# The runtime API image intentionally omits development tools. Install them in
# the disposable running container, then run the complete backend checks.
docker compose exec api sh -lc "pip install -e '.[dev]' && pytest -q && ruff check app tests alembic/versions && mypy app"

# Run frontend checks from the source tree; the final web runtime image is a
# minimal standalone image and is not a lint/test environment.
corepack pnpm --dir frontend install --frozen-lockfile
corepack pnpm --dir frontend lint
corepack pnpm --dir frontend typecheck
corepack pnpm --dir frontend test
corepack pnpm --dir frontend build

# Verify the deployed database is at migration head (0006_user_scoped_reports).
docker compose exec api alembic current
```

The Apify tests use synthetic Actor responses and never start paid jobs. SQLite is supported for fast backend tests; Docker uses PostgreSQL.

## Production limitations

- Billing, multi-tenant client workspaces, collaboration and alerts are not production-connected.
- The browser has a real per-browser JWT session boundary, but the seeded local account is not production identity, tenancy, SSO or workspace authorization.
- Background monitoring is not scheduled. `toy-refresh --due [--limit N]` can produce a read-only plan and grouped preflights, bounded by the configured provider URL limit and a hard maximum of 20; an authorised operator must still review the selected canonical URLs and add the exact confirmation flag before any provider run.
- Stored watchlist definitions are currently read-only in the toy API. The older browser watchlist editor uses local storage and does not change provider discovery.
- Account region is a provider/account field, not audience geography.
- Creator follower count is stored only when the provider actually returns it.
- Music commercial-use rights remain unknown unless verified outside the connector.
- AI or rules-based interpretations must stay labelled as derived analysis, separate from observed provider facts.
- Draft legal/trust pages still require qualified EU/UK counsel and verified operator details before publication.
