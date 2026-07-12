# Licensed provider integration

1. Complete legal/procurement review covering collection method, commercial use, retention, deletion and onward display.
2. Implement every method in `Provider` using only vendor-documented endpoints.
3. Map responses into `ProviderVideo`/`MetricPoint`; populate retrieval time, provider freshness, confidence, raw reference and missing fields.
4. Keep secrets in environment/Secret Manager and redact auth headers/query values.
5. Add fixture-based mapping, timeout, retry, rate-limit, pagination, schema-drift and health tests.
6. Register the adapter in `provider_factory`; run in shadow mode and compare against manual Creative Center validation before enabling recommendations.

TODO(provider): vendor name, API documentation, base URL, auth scheme, scopes, quotas, pagination, freshness guarantees, field semantics and licensed retention remain intentionally unspecified.

