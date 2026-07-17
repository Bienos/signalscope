# Toy Data Quality Controls

## Quality objective

No recommendation should look more certain than its evidence. SignalScope keeps availability, provenance, freshness, completeness, continuity, and contradictions visible from provider ingestion through reports.

## Required controls

### Availability

- Missing numeric fields remain null.
- `missing_fields` identifies every unavailable expected field.
- A real zero remains distinguishable from unavailable.
- Deleted, private, unavailable, partial, and active content states are explicit.

### Provenance

Every snapshot links to a provider run where available. Every run records provider, Actor, collection type, collection market, query provenance, external run/dataset identifiers, timestamps, result accounting, cost, schema fingerprint, and redacted errors.

### Identity and deduplication

- Provider identity and provider-specific ID form the stable identity boundary.
- A video observation is unique for the video, collection timestamp, source, and run context.
- Duplicate dataset rows are counted and do not create duplicate snapshots.
- Quarantined invalid rows retain only safe diagnostic context.

### Freshness

Freshness is computed from the last successful observation, not the page-render time. States are `Fresh`, `Stale`, or `Unavailable`; `DEMO TOY DATA` is a separate provenance/mode label, not a freshness value. Thresholds are configurable and shown to users.

### Continuity

- Velocity needs two usable observations.
- Acceleration needs three.
- Missing intervals appear as gaps.
- Metric decreases are flagged as contradictory evidence.
- A deleted/private result is confirmed once before terminal status where live monitoring is configured.

The refresh cadence is currently a planning policy, not a running monitor. `toy-refresh --due
[--limit N]` prepares a read-only plan and market-grouped preflights, excludes demo/mixed evidence,
non-candidate/unsaved signals and invalid canonical URLs, and clamps selection to the configured
provider per-request URL limit plus a hard maximum of 20. A single +24-hour terminal confirmation is allowed; two consecutive terminal observations stop
planning. No scheduler, queue or automatic provider call is wired, and every refresh still requires
an authorised exact confirmation.

### Provider health

The current provider context is resolved from configured mode, selected persisted source identity, the
latest matching run, last successful observation and missing-field rate. Run, data-health and cost
endpoints separately expose invalid/duplicate counts, quarantine and recorded budget use. These values
are not yet combined into one production health score.

Persisted provider identity also enforces mode isolation: demo configuration hides provider evidence;
provider mode selects only matching provider evidence where available; and a fallback to synthetic
evidence remains explicitly labelled demo. Signals and report opportunities from different modes are
not combined.

## Quarantine

One invalid Actor record must not fail the whole dataset. Quarantine entries include run, item position or safe reference, error category, redacted summary, schema fingerprint, and timestamp. Raw media and secrets are never placed in quarantine.

## Recommendation pause conditions

Pause or downgrade recommendations when:

- provider is unavailable or stale beyond policy
- required views observations are missing
- cohort size is inadequate
- missing-field rate exceeds the configured threshold
- schema fingerprint changes unexpectedly
- collection market is unknown or inconsistent
- contradictory evidence materially changes the calculation
- configured budget is reached

The UI states the decision impact and next step.

Current boundary: several pause conditions are exposed as quality or limitation text, but there is no
central automated circuit breaker that blocks every recommendation path. Analysts must treat stale,
partial, schema-drifted or budget-incomplete states as a manual stop until that enforcement exists.

## Data-health screen

Show:

- current mode and provider state
- last success and observation
- metric completeness
- successful/partial/failed runs
- duplicate, invalid, and quarantine rates
- schema drift
- markets and languages observed
- cost versus budget
- recommendation pause state

Do not hide material quality problems behind a generic system-status label.
