# Toy API Contracts

All endpoints are under `/api`. Product contracts are provider independent and use explicit nullable values. Raw Apify field names are forbidden outside the Apify package.

## Authentication and current session boundary

Every toy route requires a bearer JWT from `POST /api/auth/token`. Provider-operation routes additionally require `role=admin`. Local Compose explicitly enables labelled fixture fallback for unauthenticated **reads** only. The frontend login exchanges credentials server-side, stores the short-lived backend JWT in an HTTP-only same-site cookie, and forwards that session for allow-listed mutations and owner-scoped exports. It never auto-authenticates every visitor as the seeded administrator. This is a browser-user session boundary, but it is not yet tenancy, SSO or a production identity layer. The browser proxy does not expose provider-operation routes.

## Common response fields

- `mode`: `demo`, `live`, or `unavailable`
- `mode_label`: user-facing state such as `DEMO TOY DATA`
- `coverage`: configured monitored-sample limitation
- `provider`: provider identity and health context
- timestamps: ISO 8601 UTC values
- unavailable metrics: JSON `null`, never zero or an empty string

## Read resources

### `GET /api/toys/overview`

Returns provider state, since-last-review changes, Act/Monitor/Avoid queues, market pulse, and report readiness.

### `GET /api/toys/signals`

Filters:

- `market`
- `language`
- `category`
- `mechanism`
- `lifecycle`
- `decision`
- `confidence`
- `safety`
- `q`
- `limit`

Returns `{items, total, mode, mode_label, coverage}`.

Current implementation note: the route does not yet accept a freshness filter or offset cursor even
though freshness is returned on every signal. Pagination beyond the bounded `limit` is post-MVP.

### `GET /api/toys/signals/{signal_id}`

Returns signal summary plus:

- representative video evidence
- relationships
- evidence quality
- risks
- current saved decision
- current saved opportunity

### Supporting resources

- `GET /api/toys/videos`
- `GET /api/toys/creators`
- `GET /api/toys/hashtags`
- `GET /api/toys/sounds`
- `GET /api/toys/watchlists` (read-only configured definitions)
- `GET /api/toys/opportunities`
- `GET /api/toys/reports`
- `GET /api/toys/data-health`

## Decision workflow

### `POST /api/toys/signals/{signal_id}/decision`

```json
{
  "decision": "Act",
  "reason": "Independent creator adoption is accelerating.",
  "analyst_note": "Validate with the client before production.",
  "review_date": "2026-07-15"
}
```

Allowed decisions are `Act`, `Monitor`, and `Avoid`.

### `POST /api/toys/signals/{signal_id}/notes`

Updates the analyst note without inventing a decision.

### `POST /api/toys/signals/{signal_id}/save`

Creates or updates a saved opportunity linked to the source signal.

### `POST /api/toys/signals/{signal_id}/create-brief`

Creates a source-linked draft. All originality and safety confirmations default to false.

### `POST /api/toys/reports`

Creates or refreshes a decision-led report from opportunities explicitly marked for inclusion.

Selection is never inferred from a score. `POST .../save` must set `include_in_report=true`, or the
report request must provide `include_opportunity_ids`. Supplied IDs are still filtered to the
authenticated owner and the currently selected evidence mode. If neither is supplied, only the
owner's opportunities already marked for inclusion are used.

Migration `0006_user_scoped_reports` adds `daily_reports.user_key` and changes uniqueness from date
alone to `(report_date, user_key)`. Report list, detail, review and export queries all require the
authenticated user's key and return 404 for another user's report.

Current watchlist limitation: the stored toy watchlist read route returns enabled definitions but is
not yet filtered by authenticated user and has no create/update/delete API. Treat it as seeded
single-user configuration only. The older browser-local watchlist editor does not configure provider
discovery.

## Evidence-mode isolation

Read resources resolve a selected evidence mode from configuration and persisted provider identity.
Demo mode never exposes stored provider evidence. Live mode uses provider evidence when available;
otherwise only an explicitly labelled demo fallback can appear. Signals carry provider/mode identity,
collection envelopes remove mismatched evidence, and reports exclude opportunities whose source mode
does not match the current mode.

## Provider operations

Provider execution endpoints require administrator authorization.

### `POST /api/providers/apify/preflight`

Never starts an Actor. Returns:

- exact Actor and payload
- collection type and market
- maximum result count
- estimated maximum cost and pricing assumption
- monthly spend and configured cap
- media/comment/follower controls
- token/log/frontend safety confirmation
- whether the generated payload passes the mandatory safety assertions

### Execution

- `POST /api/providers/apify/discover`
- `POST /api/providers/apify/refresh`

Both require explicit confirmation plus enabled live configuration. No route is called during app startup, health checks, tests, or CI.

The discover and refresh routes return `executed=false` plus the preflight when confirmation is
absent. A paid call requires all of: administrator JWT, `APIFY_ENABLED=true`,
`TOY_PROVIDER_MODE=live`, a backend token, a safe bounded request, available configured budget and
`confirm_live_run=true`.

### Inspection

- `GET /api/providers/apify/runs`
- `GET /api/providers/apify/health`
- `GET /api/providers/apify/costs`

## Errors

Errors use an actionable `detail` and never include an API token. Expected statuses include:

- `400` invalid collection or payload
- `401` unauthenticated
- `403` non-admin or live execution not explicitly permitted
- `404` unknown signal/resource
- `409` insufficient evidence or incompatible state
- `422` invalid provider record or request
- `429` provider rate limit or configured budget limit
- `502` provider authentication/response failure
- `503` provider disabled or unavailable
- `504` provider timeout
