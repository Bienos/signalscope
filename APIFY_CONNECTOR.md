# Apify TikTok connector

SignalScope has a disabled-by-default, backend-only Apify provider for bounded toy,
parent and gift-buyer research. It uses Apify's maintained Python client and does not
claim complete TikTok coverage or predict virality.

Configured Actors:

- Primary: `apidojo/tiktok-scraper-api` for keyword searches, hashtag URLs, selected
  profiles, recent creator posts and canonical post-URL refreshes.
- Automatic fallback: `clockworks/tiktok-scraper`, used only after a primary request,
  run, timeout, rate-limit or output-schema failure.
- Optional expansion: `clockworks/tiktok-discover-scraper`. This is disabled by
  default because it is an additional paid run, not a fallback.

Clockworks is not called after a successful API Dojo run. Authentication,
configuration and exhausted-budget errors do not trigger fallback because another
Actor cannot correct them. A valid empty API Dojo dataset is treated as a valid empty
result rather than a reason to spend money on fallback.

Official references:

- https://docs.apify.com/api/client/python/reference/class/ApifyClient
- https://docs.apify.com/api/client/python/reference/class/ActorClient
- https://apify.com/apidojo/tiktok-scraper-api/input-schema
- https://apify.com/apidojo/tiktok-scraper-api
- https://apify.com/clockworks/tiktok-scraper/input-schema
- https://apify.com/clockworks/tiktok-scraper/output-schema

## Safety and cost controls

API Dojo receives only its documented `keywords`, `startUrls`, `sortType`, `location`,
`dateRange`, `maxItems` and `includeSearchKeywords` fields. SignalScope never sends a
custom mapping function and never persists media, avatar, cover, audio or subtitle
fields returned in its dataset.

Clockworks fallback requests explicitly disable video, cover, slideshow, avatar and
music-cover downloads; subtitles/transcription; comment bodies/replies;
follower/following lists; and related-result expansion. Comment counts remain
engagement metadata.

`max_items` and `max_total_charge_usd` are passed to the official client for every
Actor run. Fallback has a separate, lower charge ceiling. Preflight shows both the
primary cap and the maximum combined primary-plus-fallback exposure. Tests use
synthetic fixtures and never contact Apify.

## Configuration

Keep mock mode until legal, procurement, retention and display-rights checks are complete:

```dotenv
PROVIDER_TYPE=mock
APIFY_ENABLED=false
TOY_PROVIDER_MODE=demo
APIFY_TOKEN=
```

For an explicitly authorised backend deployment:

```dotenv
PROVIDER_TYPE=apify
APIFY_ENABLED=true
TOY_PROVIDER_MODE=live
APIFY_TOKEN=<backend-secret>

APIFY_PRIMARY_ACTOR_ID=apidojo/tiktok-scraper-api
APIFY_FALLBACK_ACTOR_ID=clockworks/tiktok-scraper
APIFY_ENABLE_FALLBACK=true
APIFY_FALLBACK_MAX_TOTAL_CHARGE_USD=0.50

APIFY_DISCOVER_ACTOR_ID=clockworks/tiktok-discover-scraper
APIFY_ENABLE_DISCOVER=false

APIFY_MAX_ITEMS_PER_RUN=20
APIFY_MAX_TOTAL_CHARGE_USD=0.50
APIFY_MAX_RETRIES=3
APIFY_RUN_TIMEOUT_SECONDS=600
APIFY_DEFAULT_MARKET=GB
APIFY_DEFAULT_LANGUAGE=en
APIFY_SEARCH_QUERIES=children's toys,STEM toys,sensory toys
APIFY_HASHTAGS=toys,stemtoys,sensorytoys
APIFY_PROFILES=selected_toy_creator
APIFY_POST_URLS=
```

Never put the token in a `NEXT_PUBLIC_*` variable or commit it. Blank query and
hashtag overrides use the versioned taxonomy in
`backend/app/domain/toys/seeds.json`.

Keep `APIFY_ENABLE_DISCOVER=false` when Clockworks must be fallback-only. Enabling it
adds a separate paid hashtag-expansion run even when API Dojo succeeds.

## Execution

Starting the API or frontend never runs an Actor. All paid paths require live provider
configuration plus explicit confirmation:

```bash
docker compose exec api python -m app.cli apify-config-check
docker compose exec api python -m app.cli toy-discover
docker compose exec api python -m app.cli toy-discover --confirm-live-run
docker compose exec api python -m app.cli toy-refresh --url=https://www.tiktok.com/@user/video/123 --confirm-live-run
```

The first `toy-discover` command is preflight-only. Review both charge ceilings,
Actor inputs and safety assertions before using the confirmation flag.

## Normalized field maps

Provider-specific names stop at `backend/app/providers/apify/schemas.py` and
`normalizer.py`.

| API Dojo output | SignalScope field | Handling |
|---|---|---|
| `id`, `postPage` | video ID and canonical URL | Required identity |
| `channel.id`, `channel.username` | creator ID and username | Required identity |
| `title` | caption | Missing remains explicit |
| `uploadedAtFormatted` / `uploadedAt` | published time | ISO value preferred |
| `views`, `likes`, `comments`, `shares`, `bookmarks` | immutable snapshot metrics | Missing remains SQL `NULL` |
| `hashtags` | hashtags | Normalized without `#` |
| selected `song.*` fields | sound metadata | Audio and cover URLs ignored |

| Clockworks output | SignalScope field | Handling |
|---|---|---|
| `id`, `webVideoUrl` | video ID and canonical URL | Required identity |
| `authorMeta.id`, `authorMeta.name` | creator ID and username | Required identity |
| `text`, `textLanguage` | caption and provider language | Missing remains explicit |
| `locationCreated` | creator/account content-origin field | Never audience geography |
| `playCount`, `diggCount`, `commentCount`, `shareCount`, `collectCount` | immutable snapshot metrics | Missing remains SQL `NULL` |
| `hashtags[].name`, selected `musicMeta.*` | hashtag and sound metadata | Media URLs ignored |

Every accepted record stores a token-free `apify://` reference, Actor run ID, dataset
ID, collection type, query provenance, market, schema fingerprint and missing fields.
Fallback success records both Actor IDs and the primary failure category. Missing
metrics are never converted to zero.

## Testing

```bash
cd backend
pip install -e '.[dev]'
pytest -q
ruff check .
mypy app
```

CI must not use a real token or start a paid Actor. A production smoke test requires
separate authorisation and very small item, primary-charge and fallback-charge caps.
