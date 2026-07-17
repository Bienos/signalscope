# Architecture

The API owns ingestion, storage and domain logic. Providers emit normalised records with provenance, freshness, confidence and missing-field lists. Collection upserts identities but only appends metric snapshots. The analytics service derives interval metrics, cohort percentiles, AVS/EVS/NPS, anomaly adjustment and confidence. Rule classification and safety checks work offline; an optional versioned AI adapter may enrich results without blocking the pipeline. Reports persist a reproducible JSON payload and export to HTML/CSV/email.

Trust boundaries: credentials stay server-side and are redacted; imported files are schema/size validated; no media is downloaded; all mutations require authentication; administrator-only settings/deletion actions are audited.
