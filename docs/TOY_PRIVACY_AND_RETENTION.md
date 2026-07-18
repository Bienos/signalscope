# Toy Privacy and Retention

This document is an engineering policy, not legal advice. Qualified UK/EU counsel must approve the final commercial design, lawful basis, notices, contracts, and retention schedule.

## Data minimisation

Collect only what the toy decision workflow needs:

- public provider/video/creator/hashtag/sound identifiers
- canonical public source links
- captions and metadata where contractually permitted
- publication and observation timestamps
- nullable engagement metrics
- provider-supplied account region, clearly labelled
- deterministic toy classification, safety state, and review history

Do not collect or store:

- downloaded videos or audio
- covers, avatars, or slideshow images
- comments or transcripts
- follower or following identity lists
- inferred creator age, child identity, audience age, or audience geography
- sensitive audience profiling

## Purpose limitation

Data is processed to identify and explain toy-content momentum in a configured monitored sample, support human decisions, create original briefs, and generate evidence-led reports. It is not used to identify children, target vulnerable families, determine fraud, or make automated eligibility decisions about people.

## Retention

Retention is configuration- and contract-dependent. Defaults must remain conservative:

- raw provider payload: no product-table storage; short diagnostic retention only where contractually allowed
- quarantine diagnostics: short, redacted retention
- captions and public identifiers: bounded retention aligned to customer purpose
- metric snapshots and derived signal history: retained only as permitted by the provider agreement
- deleted/private/takedown content: tombstone identity and remove displayable content promptly
- user decisions and reports: retained per workspace/customer agreement

The configured retention job must be auditable and must not silently preserve media or secret-bearing payloads.

Current implementation boundary: retention values are configuration/policy only; no automated
retention worker has been verified. Do not rely on configuration values as proof that deletion has
occurred.

## Individual rights and deletion

Maintain a documented path for access, objection, correction, deletion, and provider-synchronised removal where legally required. Existing deletion tooling should be extended to creator and canonical video identifiers without exposing private data.

## Security

- APIFY_TOKEN is backend-only and represented as a secret value.
- Tokens are sent in the Authorization header, never a URL.
- Errors, logs, provider-run summaries, and quarantine records are redacted.
- Frontend bundles, `NEXT_PUBLIC_*` variables, exports, and reports must never contain provider credentials.
- Provider execution routes require administrator authorization and explicit live confirmation.

The local Next.js demo uses a shared seeded backend account. Migration
`0006_user_scoped_reports` scopes report list/detail/review/export records to a `user_key`, but all
demo browsers act as the same user. Stored watchlist reads are not yet user-filtered, and the older
watchlist editor uses browser local storage. None of these surfaces is a production tenant boundary.

## Commercial gate

Do not offer live customer-facing analytics until a written provider agreement permits commercial use, multi-tenant display, repeated storage, derived metrics, identifiers, relevant captions/links, exports, UK/EEA processing, subprocessors, retention, deletion, and platform-policy changes.

Before commercial launch, qualified UK/EU counsel and the operator must also confirm:

- the controller/processor roles, lawful basis, privacy notices, DPA/SCC or UK transfer mechanism,
  subprocessor list and whether a DPIA is required;
- verified legal entity/contact details, data-subject and takedown procedures, retention execution,
  incident response and security controls;
- TikTok/platform terms and Apify/Actor rights for discovery, repeated observation, derived analytics,
  customer display, client reports, export and redistribution;
- copyright, trade mark, licensed-character, commercial music and source-attribution rules;
- toy safety, advertising and educational/developmental-claim review, plus child-privacy safeguards;
- deletion/private-content synchronization and what historical evidence may legally remain.

A provider token, a successful scrape or a public URL does not grant these rights.

Apify is not an official TikTok API. SignalScope is independent and is not affiliated with TikTok or ByteDance.
