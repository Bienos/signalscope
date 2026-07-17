# Apify TikTok connector

SignalScope includes a disabled-by-default backend adapter for the Apify Actor
`clockworks~tiktok-scraper`. It is deliberately limited to toy, parent and gift-buyer
research. It does not provide complete TikTok coverage and does not predict virality.

The adapter uses Apify's synchronous Actor endpoint with bearer authentication. Official
references:

- https://apify.com/clockworks/tiktok-scraper/input-schema
- https://apify.com/clockworks/tiktok-scraper/output-schema
- https://docs.apify.com/api/v2/act-run-sync-get-dataset-items-post

## Safety and cost controls

Every run forces these settings:

- video, cover, slideshow, avatar and music-cover downloads are off;
- subtitle download and transcription are off;
- comment-body and reply collection are zero;
- follower and following list collection are zero;
- related-video and related-search expansion are off;
- search is restricted to the video section;
- `maxItems` and `maxTotalChargeUsd` cap exposure.

Comment counts are retained as engagement metadata. Comment bodies are ignored even if a
provider response unexpectedly contains them. Media URLs, avatars, covers, audio URLs and
download addresses are not represented in the SignalScope provider model and are discarded.

Paid Actor POSTs are not retried automatically. A retry after an ambiguous timeout could create
a second paid run. Failed runs are recorded in `provider_runs`; existing observations remain
available.

## Configuration

Keep `PROVIDER_TYPE=mock` and `APIFY_ENABLED=false` until procurement, terms, retention and
cost checks are complete. Never put the token in a `NEXT_PUBLIC_*` variable.

Set backend-only environment values:

```dotenv
PROVIDER_TYPE=apify
APIFY_ENABLED=true
APIFY_TOKEN=<your-token>
APIFY_ACTOR_ID=clockworks~tiktok-scraper
APIFY_SEARCH_QUERIES=children's toys,STEM toys,sensory toys
APIFY_HASHTAGS=toys,stemtoys,sensorytoys
APIFY_PROFILES=selected_toy_creator
APIFY_POST_URLS=
APIFY_RESULTS_PER_PAGE=25
APIFY_MAX_ITEMS=100
APIFY_MAX_TOTAL_CHARGE_USD=2.0
APIFY_TIMEOUT_SECONDS=180
APIFY_PROXY_COUNTRY_CODE=None
```

Those two lists are optional, explicit overrides. Leave them blank to use the
versioned toy discovery taxonomy in `backend/app/domain/toys/seeds.json`.

`APIFY_PROFILES` accepts selected usernames. `APIFY_POST_URLS` accepts full TikTok post URLs for
scheduled refreshes. Comma-separated values are trimmed and de-duplicated. Keep the query and
hashtag lists inside the approved toy scope.

Apply migrations before collection. The migration chain includes a compatibility marker for local
databases that previously applied the now-reverted opportunities migration; it removes that legacy
table if it remains:

```bash
docker compose exec api alembic -c /app/alembic.ini upgrade head
```

Then run one explicitly authorised collection:

```bash
docker compose exec api python -m app.cli collect
```

The collection command is the only shipped path that starts the configured provider. Starting
the API or frontend does not run Apify.

## Field mapping

Clockworks names exist only in `backend/app/providers/apify_tiktok.py`.

| Apify output | SignalScope field | Notes |
|---|---|---|
| `id` | `ProviderVideo.id` | Required identity |
| `webVideoUrl` | `ProviderVideo.url` | Official TikTok link only |
| `authorMeta.id` | `creator_id` | Required identity |
| `authorMeta.name` | `username` | Required identity |
| `text` | `caption` | Empty when absent and marked missing where relevant |
| `textLanguage` | `language` | `und` sentinel when absent |
| `locationCreated` | `market` | Content creation location, never audience geography |
| `createTimeISO` / `createTime` | `published_at` | ISO value preferred |
| `playCount` | snapshot `views` | Null when absent |
| `diggCount` | snapshot `likes` | Null when absent |
| `commentCount` | snapshot `comments` | Count only; no comment bodies |
| `shareCount` | snapshot `shares` | Null when absent |
| `collectCount` | snapshot `favourites` | TikTok saves/bookmarks; null when absent |
| `hashtags[].name` | `hashtags` | Normalised without `#` |
| `musicMeta.musicId` | `sound_id` | Metadata only; no audio download |
| `musicMeta.musicName` | `sound_title` | Rights status remains unknown |

Each video persists the provider name and a token-free `apify://...` reference. Each collection
appends an immutable metric snapshot with collection time, provider freshness, source and missing
fields. Missing metrics remain SQL `NULL`; they are never converted to zero and incomplete
snapshots are excluded from scoring.

The adapter does not persist `authorMeta.fans`, `authorMeta.following`, media URLs, comments,
transcripts, TikTok Shop data, avatars, covers or full video/audio files.

## Direct URL refresh

The provider exposes `refresh_video_urls([...])`. It submits only `postURLs` and the mandatory
safety controls. `get_video_metrics([...])` returns metrics only for videos already cached by the
current provider instance; unknown IDs must first be refreshed by full URL so SignalScope never
guesses a TikTok URL.

## Testing

Tests use `backend/tests/fixtures/apify_tiktok_items.json` and `httpx.MockTransport`. They never
contact Apify or start a paid Actor.

```bash
cd backend
pytest -q
ruff check .
mypy app
```

Before production, add a separately authorised manual smoke test with a strict charge cap, confirm
the current Actor schema, review Apify/TikTok terms with counsel, and verify customer-facing display,
retention and export rights.
