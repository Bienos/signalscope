# Apify toy provider engineering notes

The production setup, safety envelope, exact environment variables and field map
are maintained in [`APIFY_CONNECTOR.md`](../APIFY_CONNECTOR.md). This file records
the internal package boundaries.

## Package structure

- `client.py` wraps the maintained synchronous `apify-client` package.
- `inputs.py` builds allow-listed Actor inputs and fail-closed safety assertions.
- `schemas.py` is the boundary for API Dojo and Clockworks output field names.
- `normalizer.py` converts Actor results to provider-independent `ProviderVideo`
  records and quarantines invalid items without retaining raw payloads.
- `costs.py` enforces per-run and monthly planning caps.
- `capabilities.py` reports supported and deliberately unsupported features.
- `provider.py` implements the existing SignalScope Provider protocol.

## Actor responsibilities

- `apidojo/tiktok-scraper-api`: primary keyword, hashtag, selected-profile and
  canonical post-URL collection.
- `clockworks/tiktok-scraper`: automatic fallback after retryable primary failures.
- `clockworks/tiktok-discover-scraper`: optional hashtag-led expansion only and
  disabled by default.

All names are environment-controlled but limited to implemented schema contracts.
The primary Actor remains responsible for selected creator posts; there is no
separate profile-enrichment Actor in this phase.
The TikTok Trends Scraper is not integrated.

## Evidence behavior

Each run persists Actor/run/dataset provenance, collection scope, item counts,
missing-field rate, schema fingerprints and provider-reported cost where available.
Every observation appends an immutable snapshot. Missing metrics remain `NULL`.
Fallback evidence records both Actor IDs and a redacted failure category. Discover
output preserves normalized seed and related-tag context alongside the
associated creators and sounds present in accepted video records.

No media, comment bodies, follower/following identities or transcripts are persisted
by SignalScope. Collection market and creator/account origin are never described as
audience geography.

## Tests

Tests inject a synthetic object implementing the official client's Actor/Dataset/User
surface. They do not use a token, contact Apify or start paid runs.

```bash
cd backend
pip install -e '.[dev]'
pytest -q
ruff check .
mypy app
```
