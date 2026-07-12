# SignalScope

Private, provider-independent trend intelligence for a monitored sample of TikTok posts. The app never scrapes TikTok or stores video media: it uses deterministic mock data, validated CSV/JSON imports, or a contractually authorised REST provider and displays official links.

## Quick start

```bash
cp .env.example .env
docker compose up --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.cli seed
```

Open http://localhost:3000 and sign in with `admin@viralradar.local` / `RadarDemo!2026` (local seed mode only). API docs are at http://localhost:8000/docs.

The commercial demo is at http://localhost:3000/pricing. It includes provisional Free Preview, Pro, Team and Enterprise packaging. Users choose categories through local demo watchlists: Free includes one, Pro five and Team twenty. Toys remains a selectable category rather than a standalone paid pack. Hashtag Research and Sound Intelligence remain optional depth add-ons. Plan switching and upgrade gates demonstrate the intended product experience only: billing, persistent subscriptions and server-enforced customer entitlements are not connected.

Draft legal and trust pages are available at http://localhost:3000/legal. They intentionally contain publication-blocking placeholders for the legal operator, contacts, jurisdiction, vendors and commercial terms. See [LEGAL_IMPLEMENTATION_REVIEW.md](LEGAL_IMPLEMENTATION_REVIEW.md). These drafts are not legal advice and must be reviewed by qualified EU/UK counsel before publication.

Run a mock collection or report:

```bash
docker compose exec api python -m app.cli collect
docker compose exec api python -m app.cli report
```

Local email writes HTML to `outputs/mail/`. Report HTML/CSV exports are available from the Reports screen and API.

All seeded values are **Demo data**. The dashboard distinguishes collection time from provider freshness, exposes score evidence and cohort size, and uses one safety-aware eligibility contract for emerging posts. Hashtag and sound lifecycle remain “Insufficient history” until time-bucketed observations from a licensed provider are available.

## Architecture

Next.js dashboard -> FastAPI modular monolith -> PostgreSQL. A separate worker invocation runs discovery, immutable snapshots, calculations, classification, clustering and reporting. Provider, AI and email boundaries are protocols. See [ARCHITECTURE.md](ARCHITECTURE.md), [PROVIDER_INTEGRATION.md](PROVIDER_INTEGRATION.md), [SCORING.md](SCORING.md), [DATA_DICTIONARY.md](DATA_DICTIONARY.md), and [COMPLIANCE.md](COMPLIANCE.md).

## Development

```bash
cd backend && pip install -e '.[dev]' && pytest && ruff check . && mypy app
cd frontend && pnpm install && pnpm lint && pnpm build
```

SQLite is supported for fast local tests (`DATABASE_URL=sqlite:///./radar.db`); Docker uses PostgreSQL. Seed creates 120 videos, 36 creators, 24 sounds, 48 hashtags, and four snapshots per video so every dashboard is populated.

## Schedules

Run `python -m app.cli collect` at 00:00, 06:00, 12:00 and 18:00; `score` at 07:00; and `report` at 07:30 Europe/Warsaw. Production should invoke these as Cloud Run Jobs or cron, not an in-process scheduler.

## Licensed provider

Implement the protocol in `app/providers/base.py`, map the vendor's documented contract, preserve provenance/missing fields, and add contract tests. No real-vendor endpoints are invented. See [PROVIDER_INTEGRATION.md](PROVIDER_INTEGRATION.md).

## Deployment

Build `backend/Dockerfile` and `frontend/Dockerfile`; point `DATABASE_URL` at Supabase PostgreSQL; store secrets in Secret Manager; deploy web/API separately to Cloud Run and commands as Cloud Run Jobs. Set frontend `API_URL` to the API service URL and restrict ingress/auth for an internal service.

## Limitations and troubleshooting

Coverage is not exhaustive. Scores describe observed provider-reported metrics, not future certainty. Commercial-use music status is unknown unless explicitly supplied. If readiness fails, verify the database, run migrations and seed. Provider failures are recorded and leave prior results available with a freshness warning.

Before selling access, obtain written provider permission for customer-facing display, storage, history, export and redistribution; validate provider unit economics; add backend-owned workspaces, subscriptions and usage enforcement; and complete legal review. Current prices are hypotheses for buyer research, not contracted offers.
