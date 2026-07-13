# Toy Trend Methodology

## Purpose

SignalScope evaluates a configured sample of public TikTok toy content. It does not rank all of TikTok and it does not predict virality. The product groups observed posts into explainable toy signals and helps an analyst decide whether to Act, Monitor, or Avoid.

## Evidence layers

Each product statement is tagged conceptually as one of:

- **Observed** — supplied directly by the configured provider, such as a canonical post URL or an engagement count at a collection time.
- **Calculated** — produced deterministically from observed values, such as views per hour.
- **Interpretation** — a reviewable explanation of why a signal may matter.
- **Human decision** — an analyst's saved Act, Monitor, or Avoid choice and note.

Interpretation never becomes observed fact. AI-supported copy, when enabled later, must remain clearly labelled and source-linked.

## Observation rules

- Snapshots are append-only.
- A missing provider value remains null and is listed in `missing_fields`.
- A real observed zero remains zero.
- Velocity requires two usable view observations with a positive elapsed interval.
- Acceleration requires three usable view observations. With fewer than three, acceleration is unavailable.
- Decreasing counters are contradictory or anomaly evidence. They are never labelled fraud automatically.
- Account region is provider-supplied creator metadata, not audience geography or collection market.

## Toy classification

The deterministic classifier and default discovery configuration load the canonical English and Polish toy taxonomy from `backend/app/domain/toys/seeds.json` through `load_toy_taxonomy()`. Environment query/hashtag values are explicit run overrides, not a second taxonomy. Frontend fallback fixtures are presentation data and are not an authoritative source of classification rules. The classifier identifies a likely product category, a likely content mechanism, and zero or more safety flags. The rules are intentionally conservative and versioned.

The classifier does not infer:

- creator age or whether a creator is a child
- child identity
- audience age
- audience geography
- educational or developmental efficacy

Uncertain classifications remain `Unknown` or require human review.

## Signal clustering

The first implementation uses collection market, toy category, and content mechanism as an explainable cluster key. Hashtag overlap, sound identity, and caption-pattern evidence support the cluster but do not override the primary market/category/mechanism context. Videos remain attached as inspectable evidence.

This approach is intentionally transparent. It is a production-shaped MVP, not a claim that every cultural relationship is captured.

## Metrics

### Velocity

```text
(current views - previous views) / elapsed hours
```

### Acceleration

```text
current interval velocity - previous interval velocity
```

### Creator spread

The number of independent observed creators supporting the signal. Creator spread is never inferred from videos that only share a null sound identifier.

### Creator baseline

A creator baseline is included only after enough comparable recent observations exist. A single post is not its own baseline. When the minimum is not met, the baseline component is listed as missing.

### Hashtag momentum

Hashtags are evaluated within the toy sample using observed posts, independent creators, creator growth, associated post velocity, collection-market spread, freshness, and saturation. Accumulated post count alone is not momentum.

Current supporting-entity boundary: the API exposes observed posts, independent creators,
categories, mechanisms, related tags, market and freshness. It leaves `creator_growth` null until
repeated hashtag-cohort history exists, and uses only conservative `Insufficient evidence`/`Emerging`
labels. It does not fabricate a hashtag growth curve.

### Sound momentum

Sounds are evaluated using new toy posts, independent toy creators, category spread, associated post velocity, freshness, and saturation. Sound metadata is not music-rights clearance; rights status defaults to `Unknown`.

The current sound view exposes observed toy-post adoption, independent creators, category spread and
median associated post velocity where available. It does not yet persist a separate sound-adoption
time series, so its lifecycle remains conservative.

### Saturation

Saturation increases when a mechanism is broadly adopted, creator concentration is low, post volume is high, and acceleration is flattening. It is an observed-sample differentiation indicator, not a platform-wide share estimate.

## Lifecycle

| Lifecycle | Minimum interpretation | Default response |
|---|---|---|
| Insufficient evidence | Not enough repeated observations or creator spread | Wait |
| Emerging | Early positive evidence across a small independent set | Monitor |
| Accelerating | Interval velocity and adoption are increasing | Investigate or test |
| Breakout | Strong multi-creator acceleration with a usable decision window | Act |
| Viral | High observed distribution and broad adoption | Use selectively |
| Saturated | Broad adoption with low differentiation or flattening | Avoid direct imitation |
| Declining | Momentum has passed its recent peak | Do not prioritise |
| Recurring | A previously observed active pattern reappears after a separated observation window with positive re-acceleration | Plan ahead |

One observation always produces `Insufficient evidence`.

## Opportunity score

The Toy Opportunity Score is a versioned decision aid. Components may include:

- post velocity
- acceleration
- unique-creator growth and diversity
- toy-category relevance
- observed shares and saves
- freshness
- saturation penalty
- evidence completeness

Each result exposes component values, weights or fallbacks, missing components, cohort context, and score version. It is never described as a probability of going viral.

## Confidence

Confidence considers:

- usable snapshot count
- independent creator count
- required-field completeness
- data freshness
- cohort size
- collection-market consistency
- contradictory evidence
- provider health

Evidence from one market can still be useful, but confidence must explicitly state that no cross-market confirmation exists; it must not imply geographic spread.

Confidence is independent of opportunity score magnitude. A high score can have low confidence.

## Decision policy

- **Act** — adequate evidence, acceptable safety state, and an active decision window.
- **Monitor** — promising but missing evidence; the UI states what would move the signal to Act and when to review it.
- **Avoid** — a specific reason such as saturation, safety, weak evidence, low toy relevance, direct-imitation risk, copyright risk, or music-rights uncertainty.

Every saved decision has fields for reason, analyst note, and review date. A quick queue action may
persist an empty reason before analysis; it must not be treated as a completed analyst rationale.
Every opportunity and creative brief retains its source signal.

## Selected-video monitoring policy

Discovery and monitoring remain separate. Keyword, hashtag, and approved-profile runs find candidates; only selected canonical video URLs are eligible for direct refresh.

- New low-potential post: one follow-up at +24 hours.
- Candidate: +6 and +24 hours.
- Strong accelerating or breakout candidate: +1, +6, +24, and +72 hours.
- Saturated or declining post: stop unless it was explicitly saved; a saved item receives one +24-hour follow-up.
- Deleted/private/unavailable: confirm once at +24 hours, then treat the state as terminal.

The executable default is `app.domain.toys.refresh_offsets_hours`. It selects a bounded schedule; it never starts a provider run itself. `python -m app.cli toy-refresh --due [--limit N]` turns due rows into a read-only plan and market-grouped preflights. It excludes demo/mixed evidence, non-candidate/unsaved signals and invalid canonical URLs. The applied limit is the smallest of the CLI request, configured provider per-request URL limit and hard cap of 20; output exposes the CLI and provider limits. `--limit` is accepted only with the exact boolean `--due`, must be positive, and `--due=value` is rejected. Without the exact `--confirm-live-run` flag, no provider request is made. There is no background scheduler, queue worker or automatic alert delivery.

Terminal/private/deleted/unavailable evidence receives at most one +24-hour confirmation; two consecutive terminal observations stop further planning. An authorised operator must still review every selected canonical URL and explicitly confirm any run. Merely saving a post or calculating an offset never contacts Apify.

`Recurring` is also conservative: it requires a persisted prior active lifecycle, at least a 72-hour gap to a new observation window, and positive re-acceleration. A label cannot become Recurring merely because the same category/mechanism is present in one continuous fixture window.
