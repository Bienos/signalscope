# First Controlled Apify Test

The default procedure below stops at a local preflight. It does not contact Apify and cannot start a paid Actor. A live run is a separate, manual step for an authorised administrator only after written rights, budget and the exact preflight have been approved.

## Preconditions

1. Run `docker compose exec api alembic upgrade head`; head must be `0006_user_scoped_reports`.
2. Seed the local administrator with `docker compose exec api python -m app.cli seed`.
3. Keep `PROVIDER_TYPE=mock`, `APIFY_ENABLED=false`, `TOY_PROVIDER_MODE=demo` and `APIFY_TOKEN=` while performing the no-paid phase.
4. Do not use `toy-discover` for the first controlled run: blank CLI overrides load the complete central keyword and hashtag taxonomy. Use the resource-specific preflight below.
5. Before any later live step, obtain written permission for the test, confirm the Apify account budget, and verify the current Actor schema and price.

## Phase A — exact no-paid preflight

Obtain a local administrator token without printing it:

```bash
ADMIN_TOKEN="$(
  curl -fsS -X POST http://localhost:8000/api/auth/token \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode 'username=admin@viralradar.local' \
    --data-urlencode 'password=RadarDemo!2026' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"
```

Request one GB keyword with a five-result bound:

```bash
curl -fsS -X POST http://localhost:8000/api/providers/apify/preflight \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{
    "collection_type": "keyword",
    "market": "GB",
    "values": ["educational toys"],
    "max_results": 5
  }' > /tmp/signalscope-apify-preflight.json
```

Assert the safety envelope locally:

```bash
python3 - <<'PY'
import json

value = json.load(open('/tmp/signalscope-apify-preflight.json'))
assert value['executed'] is False
assert value['confirmation_required'] is True
preflight = value['preflight']
assert preflight['actor_id'] == 'clockworks~tiktok-scraper'
assert preflight['collection_type'] == 'keyword_discovery'
assert preflight['market'] == 'GB'
assert preflight['maximum_result_count'] == 5
assert preflight['safe_to_execute'] is True
assert all(preflight['safety'].values())
assert preflight['token_in_payload'] is False
assert preflight['token_in_url'] is False
assert preflight['cost']['enforced_max_charge_usd'] > 0
print('Preflight passed; no Actor was started.')
PY
```

Stop here by default. The preflight route builds and prices the request locally; it makes no provider network request.

## Required manual review

Review `/tmp/signalscope-apify-preflight.json` and record:

- Actor and collection type;
- exact `actor_payload` and the single search value;
- `maximum_result_count=5`;
- advertised estimate, remaining monthly budget and enforced `maxTotalChargeUsd` ceiling;
- GB collection/proxy context;
- every media, subtitle/transcript, comment, follower/following, related-search/video and additional-author safeguard;
- confirmation that the token is absent from the URL, payload, logs and frontend;
- current provider terms, TikTok/platform terms, Actor input schema and current price.

Do not continue if any safeguard is false, the estimated/capped cost is unapproved, the Actor schema differs, or the intended storage and customer use are not permitted.

## Phase B — authorised live run only

This phase can incur a charge. It is not a test, CI, startup or documentation command. An authorised operator must deliberately configure the backend secret store:

```dotenv
PROVIDER_TYPE=apify
APIFY_ENABLED=true
TOY_PROVIDER_MODE=live
APIFY_TOKEN=<backend-secret>
APIFY_DEFAULT_MARKET=GB
APIFY_SUPPORTED_MARKETS=GB,PL
APIFY_MAX_RESULTS_PER_QUERY=5
APIFY_MONTHLY_BUDGET_USD=1
APIFY_PROFILE_ENRICHMENT_ENABLED=false
```

The HTTP route uses request `max_results` for `maxItems` and generates its `maxTotalChargeUsd` from
the preflight estimate and remaining configured monthly budget. The legacy
`APIFY_MAX_ITEMS`/`APIFY_MAX_TOTAL_CHARGE_USD` environment inputs affect the CLI provider only and
must not be treated as HTTP-route safeguards.

Restart the API so cached settings are replaced:

```bash
docker compose up -d --force-recreate api
```

Obtain a fresh administrator token and repeat Phase A. Compare the new preflight byte-for-byte where
practical and re-approve its generated `maxTotalChargeUsd` ceiling.

The following is the only execution step. It starts a potentially paid Actor. The exact approval phrase makes a pasted/default invocation stop before the request:

```bash
printf 'Type APPROVE ONE PAID APIFY RUN to continue: '
IFS= read -r LIVE_APPROVAL
if [ "${LIVE_APPROVAL}" != 'APPROVE ONE PAID APIFY RUN' ]; then
  echo 'Stopped; no Actor request sent.'
  exit 1
fi

curl -fsS -X POST http://localhost:8000/api/providers/apify/discover \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{
    "collection_type": "keyword",
    "market": "GB",
    "values": ["educational toys"],
    "max_results": 5,
    "confirm_live_run": true
  }' > /tmp/signalscope-apify-live-result.json
```

`confirm_live_run=true` is the paid-run boundary; omitting it returns another preflight. Never place
this execution block in CI, application startup or a scheduler. Immediately after the controlled
run, restore `APIFY_ENABLED=false`, `TOY_PROVIDER_MODE=demo`, `PROVIDER_TYPE=mock`, remove the token
from the local environment, run `docker compose up -d --force-recreate api`, and verify the demo
label. Stored provider observations remain isolated and hidden while demo mode is selected.

## Validation after an authorised run

Confirm:

1. Provider run ID, dataset ID, start/finish status, returned/accepted/duplicate/invalid counts, missing-field rate, schema fingerprint and provider-reported cost are recorded.
2. No token appears in logs, errors, URLs, database fields, exports or frontend responses.
3. No media, comments, transcripts, follower/following identities or related expansions were collected.
4. Collection market remains separate from creator account region.
5. Missing engagement values remain null.
6. Canonical links open public sources without storing media.
7. Invalid records are quarantined without discarding valid records.
8. A repeated direct-URL observation appends a snapshot instead of overwriting one.
9. Velocity requires two usable view observations; acceleration requires three.
10. The UI says configured provider sample and never complete, official or real-time TikTok coverage.

## Stop conditions

Stop if the Actor ignores item/charge ceilings, provider cost is unavailable, recorded monthly spend is incomplete, a schema changes unexpectedly, more results are returned than requested, or any safety input is not honoured. Recorded run cost is only what the provider response supplies; reconcile it with Apify billing before another run.

Do not proceed to customer-facing use without written permission for commercial display, repeated collection, history, derived metrics, identifiers/captions/links, exports, UK/EEA processing, subprocessors, retention, deletion and platform-policy changes. A technically successful Actor run is not proof of licensed coverage or commercial viability.
