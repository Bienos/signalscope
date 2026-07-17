# Apify toy provider

SignalScope contains a disabled-by-default provider for a configured sample of public TikTok toy
posts. Apify is not an official TikTok API. The connector does not provide exhaustive TikTok
coverage and its metrics are observations, not virality predictions.

No live Actor run is required for development or CI. Tests use synthetic dataset items and
`httpx.MockTransport`.

## Actors

- Primary discovery and refresh: `clockworks~tiktok-scraper`
- Optional selected-profile enrichment: `clockworks~tiktok-profile-scraper`

The optional profile Actor is disabled independently and is never invoked during broad discovery.
It may be selected only through an explicit profile request after a creator qualifies for deeper
analysis.

Actor input schemas were checked on 2026-07-13:

- <https://apify.com/clockworks/tiktok-scraper/input-schema>
- <https://apify.com/clockworks/tiktok-profile-scraper/input-schema>

The integration uses the canonical asynchronous Apify API flow documented at
<https://docs.apify.com/api/v2>: start an Actor, poll the run, then page through its default dataset.

## Configuration

```dotenv
PROVIDER_TYPE=mock
APIFY_ENABLED=false
APIFY_TOKEN=
APIFY_API_BASE=https://api.apify.com/v2
APIFY_DISCOVERY_ACTOR_ID=clockworks~tiktok-scraper
APIFY_PROFILE_ACTOR_ID=clockworks~tiktok-profile-scraper
APIFY_PROFILE_ENRICHMENT_ENABLED=false
APIFY_MAX_RESULTS_PER_QUERY=50
# Legacy CLI-only compatibility inputs. HTTP routes do not read these; their
# request max_results and generated preflight maxTotalChargeUsd are authoritative.
APIFY_MAX_ITEMS=
APIFY_MAX_TOTAL_CHARGE_USD=
APIFY_DEFAULT_MARKET=GB
APIFY_SUPPORTED_MARKETS=GB,PL
APIFY_RUN_TIMEOUT_SECONDS=900
APIFY_REQUEST_TIMEOUT_SECONDS=60
APIFY_MONTHLY_BUDGET_USD=50
APIFY_RAW_PAYLOAD_RETENTION_DAYS=14
TOY_DISCOVERY_ENABLED=true
TOY_MONITORING_PERCENTAGE=10
TOY_PROVIDER_MODE=demo
APIFY_SEARCH_QUERIES=
APIFY_HASHTAGS=
```

Blank query and hashtag values load the versioned central taxonomy from
`backend/app/domain/toys/seeds.json`. Set either variable only for an explicit,
reviewed run override; the environment is not a second copy of the seed list.
Because each blank value independently falls back to its central seed list, the CLI
`toy-discover` command can prepare both a keyword run and a hashtag run. Use the typed
`/api/providers/apify/preflight` endpoint for a first test that must contain exactly one
collection type and one source value.

Application startup is network-free. A paid run requires all of the following:

1. `APIFY_ENABLED=true`
2. `TOY_PROVIDER_MODE=live`
3. A backend-only `APIFY_TOKEN`
4. A typed request whose market is in `APIFY_SUPPORTED_MARKETS`
5. A successful safety assertion and cost preflight
6. A direct backend request authenticated as an administrator
7. The exact `confirm_live_run=true` execution boundary

Set `PROVIDER_TYPE=apify` as an operational consistency setting for CLI/factory behavior, but do not
treat it as an HTTP execution safety gate: the resource-specific Apify routes construct their adapter
directly.

The token is sent only as a bearer `Authorization` header. It is not placed in query parameters,
Actor input, provider references, exceptions or frontend variables.

## Public integration surface

Import from `app.providers.apify`:

- `ApifyProviderSettings`
- `ApifyTikTokProvider`
- `ActorRequest`, `CollectionType`, `SearchDateRange`
- `build_keyword_request`
- `build_hashtag_request`
- `build_profile_request`
- `build_direct_refresh_request`
- `estimate_cost`
- the structured `Apify*Error` classes

`ApifyTikTokProvider` exposes typed request helpers, `preflight(request)`, async
`collect(request)`, synchronous `collect_sync(request)`, direct refresh, selected-profile
collection, configuration health and an opt-in network health check. The legacy import path
`app.providers.apify_tiktok` remains available.

## Input modes

Each mode is a separate Actor run so discovery and monitoring provenance remain distinct.

Discovery does not automatically select posts for monitoring. Direct refresh accepts only canonical
URLs explicitly supplied by an authorised operator or selected by the read-only due planner.
`python -m app.cli toy-refresh --due [--limit N]` excludes demo/mixed evidence, accepts only
candidate-or-saved signals and canonical HTTPS TikTok `/video/{digits}` URLs, groups preflights by
collection market and clamps the selection to the configured per-request provider URL limit and a
hard maximum of 20 URLs. Output includes both `cli_requested_limit` and `provider_url_limit`.
`--limit` must be a positive integer and is valid only with the exact boolean `--due`; `--due=value`
is rejected, and `--due` and `--url` are mutually exclusive. With no exact
`--confirm-live-run`, the command cannot start a provider request. There is no background scheduler,
queue worker or alert delivery in this implementation.

## Evidence-mode isolation

Persisted source identity, not a UI label, determines evidence mode. `mock` and synthetic sources
remain demo evidence; non-mock provider observations remain provider evidence. When
`TOY_PROVIDER_MODE=demo`, stored provider videos and their signals are hidden. When configured live
evidence exists, only matching provider signals are selected. A live configuration with no provider
evidence may fall back only to clearly labelled demo evidence. Signal keys include provider and mode,
and report opportunities are filtered to the currently selected mode, so demo and provider evidence
are not blended into one result.

### Exact Actor input fields

The primary Actor receives these common fields in every mode:

| Field | Value or source |
|---|---|
| `resultsPerPage` | Validated per-source limit |
| `proxyCountryCode` | Validated configured collection market |
| `scrapeRelatedSearchWords` | `false` |
| `scrapeRelatedVideos` | `false` |
| `scrapeAdditionalAuthorMeta` | `false` |
| `maxFollowersPerProfile` / `maxFollowingPerProfile` | `0` |
| `commentsPerPost` / `topLevelCommentsPerPost` / `maxRepliesPerComment` | `0` |
| `shouldDownloadVideos` / `shouldDownloadCovers` | `false` |
| `shouldDownloadSlideshowImages` / `shouldDownloadAvatars` | `false` |
| `shouldDownloadMusicCovers` | `false` |
| `downloadSubtitlesOptions` | `NEVER_DOWNLOAD_SUBTITLES` |

Mode-specific primary-Actor fields are:

| Mode | Exact fields |
|---|---|
| Keyword | `searchQueries`, `searchSection=/video`, `videoSearchSorting=LATEST`, `videoSearchDateFilter` |
| Hashtag | `hashtags` |
| Selected profile | `profiles`, `profileScrapeSections=[videos]`, `profileSorting=latest`, `excludePinnedPosts=true` |
| Direct refresh | `postURLs` |

The optional profile Actor receives `profiles`, `profileScrapeSections`, `profileSorting`,
`excludePinnedPosts`, `resultsPerPage`, and only the safety fields supported by its published schema:
the follower/following limits, comment/reply limits, video/cover/slideshow/avatar download switches,
and `downloadSubtitlesOptions`. It is not sent `proxyCountryCode`, related-search switches,
additional-author expansion, or the unsupported music-cover switch.

This schema-specific allow-list was verified against the published profile Actor schema on
2026-07-13. The optional Actor remains disabled by default. Reverify the schema and generated
preflight immediately before enabling it; do not assume the primary Actor's input names are portable.

The Apify API call separately sets `timeout`, `maxItems`, `maxTotalChargeUsd`,
`restartOnError=false`, and `waitForFinish=0` as run query parameters. These are execution
ceilings and controls, not Actor input fields.

### Keyword discovery

Uses video-only search, latest sorting and a configured date window. Latest sorting and date
filtering are marked as paid Actor inputs in preflight output.

### Hashtag discovery

Uses only configured toy seed hashtags. Seed presence is not proof that a hashtag is trending.

### Selected profiles

Uses approved public usernames, latest public posts and excludes pinned posts. Broad discovery uses
the primary Actor. The optional profile Actor requires `APIFY_PROFILE_ENRICHMENT_ENABLED=true` and an
explicit `use_enrichment_actor=True` request.

### Direct video refresh

Accepts canonical HTTPS TikTok video URLs only. It does not derive or guess URLs from provider IDs.
This is the intended repeated-observation path for selected monitoring candidates.

The due planner permits one +24-hour confirmation for terminal/private/deleted/unavailable evidence,
then stops after two consecutive terminal observations. It is a plan and preflight surface, not an
automatic monitor.

## Forced safety inputs

The primary Actor always receives explicit settings that disable:

- video, cover, slideshow-image, avatar and music-cover downloads;
- subtitles and transcription;
- comment and reply collection;
- follower and following identity collection;
- related-video and related-search expansion;
- additional author-profile expansion.

The profile Actor receives the subset supported by its published schema. It does not receive
unsupported input names. No named media key-value store is created.

Comment counts remain permitted engagement metadata. Comment bodies are never represented in the
normalised provider model.

## Cost preflight

`provider.preflight(request)` returns, without making a network request:

- the exact Actor ID and payload;
- collection type and market;
- maximum result count;
- advertised per-result estimate;
- API-enforced `maxItems` and `maxTotalChargeUsd` ceilings;
- remaining configured monthly budget;
- all media/comment/follower-list safety confirmations;
- confirmation that the token is backend-header-only and redacted.

Advertised prices checked on 2026-07-13 were USD 1.70 per 1,000 results for the discovery Actor and
USD 1.00 per 1,000 results for the profile Actor. Prices and paid filter charges can change. The
catalogue estimate is therefore informational; `maxTotalChargeUsd` is the enforced run ceiling.
The API and CLI preflight sum provider-reported `ProviderRun.cost` values for the current month.
Failed or older runs without a reported cost can make that total incomplete, so it must be
reconciled with Apify billing before every additional authorised run. This is not a production
billing ledger.

## Reliability behavior

- Actor-start POST requests are never automatically retried. A timeout may be ambiguous and a retry
  could start a second paid run.
- Idempotent status, health and dataset GETs retry rate limits, `Retry-After`, transient 5xx responses,
  timeouts and transport errors.
- Actor failures, authentication failures, rate limits, timeouts, schema failures and budget failures
  have distinct exception classes and categories.
- Dataset results use offset/limit pagination and an absolute maximum item count.
- A failed/timed-out/aborted run is exposed as partial only when its default dataset contains usable
  records; the run status remains non-successful in provenance and quality output.
- Invalid records and item-level provider errors are quarantined as redacted summaries. Raw records
  are not persisted by this package.
- `APIFY_RAW_PAYLOAD_RETENTION_DAYS` is a policy/configuration value; no automated retention worker
  is wired in this implementation.

## Data and commercial limitations

- Account or content-creation region is not audience geography.
- The configured collection market is stored separately from provider account region.
- Missing metrics remain null and are listed in `missing_fields`.
- Sound metadata does not confer music-use rights; rights status remains unknown.
- No comments, transcripts, follower identities, TikTok Shop data, video, audio, covers or avatars
  are retained.
- Customer-facing display, history, export and redistribution require confirmed provider and TikTok
  terms, commercial rights and legal review.
- The local browser may read explicitly labelled fixtures without a session, but persistent actions require a per-browser JWT login; it does not proxy provider-operation routes.
  Provider preflight, execution, run, health and cost endpoints require a direct administrator JWT.

## Controlled live-test gate

Follow [TOY_LIVE_TEST_PLAN.md](TOY_LIVE_TEST_PLAN.md). Its default phase performs an exact one-keyword,
five-result preflight without contacting Apify. Only an authorised manual continuation can start an
Actor. Start with no profile enrichment and no automatic start retry, then compare returned public
links and metrics manually before allowing the evidence to inform a recommendation.
