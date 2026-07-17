# Licensed provider integration

1. Complete legal/procurement review covering collection method, commercial use, retention, deletion and onward display.
2. Keep `PROVIDER_TYPE=mock` and `APIFY_ENABLED=false` until the review is complete.
3. Store `APIFY_TOKEN` only in the backend environment or Secret Manager. Authentication uses a bearer header, never a frontend variable or URL query parameter.
4. The implemented `clockworks~tiktok-scraper` adapter maps responses into `ProviderVideo`, including retrieval time, provider freshness, confidence, token-free raw reference and missing fields.
5. Synthetic fixture tests cover mapping, safety inputs, direct URL refresh, profile discovery, immutable snapshots, null metrics and disabled-by-default behaviour. CI never runs the Actor.
6. Run a separately authorised, charge-capped smoke test and compare a small sample with manually observed TikTok/Creative Center values before enabling recommendations.
7. Monitor Actor input/output schema changes. Do not silently map new vendor fields into the domain model.

See [APIFY_CONNECTOR.md](APIFY_CONNECTOR.md) for setup, the exact field map and current limitations. Contractual display, export and retention rights, rate limits and freshness guarantees remain deployment blockers until verified.
