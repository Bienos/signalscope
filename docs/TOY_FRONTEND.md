# Toy Frontend Product Contract

## Primary workflow

The workspace is organised around decisions:

- **Today** — the daily toy brief and decision queue
- **Discover** — signal-first research with a secondary analyst table
- **Track** — watchlists, creators, hashtags, and sounds as supporting evidence
- **Opportunities** — saved Act/Monitor/Avoid decisions and source-linked briefs
- **Reports** — decision-led reports and secondary data exports
- **Workspace** — data health, methodology, settings, and plan information

Creators, hashtags, and sounds are not separate product pillars. They are research entities attached to a toy signal.

## Current demo boundary

Local Compose explicitly enables labelled synthetic-fixture fallback for unauthenticated reads. Persistent writes and exports require `/login`; the frontend exchanges credentials server-side and stores the short-lived backend JWT in an HTTP-only same-site cookie. It does not auto-authenticate visitors as the seeded administrator. This is still a local evaluation identity rather than production tenancy, SSO or a client-workspace permission model. Provider-operation routes are intentionally outside the browser proxy and require direct administrator authorization.

## Global state

Every workspace screen displays:

- `DEMO TOY DATA`, `LIVE PROVIDER SAMPLE`, or `PROVIDER UNAVAILABLE`
- collection market and language
- last successful observation
- freshness state
- provider quality state
- monitored-sample coverage limitation

Demo data is never called live. Imports are never automatically called licensed coverage.

## Today

The reading order is:

1. data usability and freshness
2. changes since the previous review
3. Act, Monitor, and Avoid queues
4. strongest market/category/mechanism changes
5. report readiness

Each queue item includes conclusion, category, mechanism, lifecycle, recommendation, decision window, confidence, freshness, main limitation, safety state, and one primary action.

## Discover

The default decision view uses signal cards or compact rows. The analyst table is secondary. Filters cover market, language, category, mechanism, lifecycle, decision, creator type, confidence, safety, freshness, and text search.

Lifecycle tabs are Emerging, Accelerating, Breakout, Viral, Saturated, Declining, Recurring, and Insufficient evidence.

## Signal detail

Signal detail contains:

- summary and conclusion
- why it is moving
- representative canonical evidence links
- related hashtags, sounds, creator types, and market differences
- evidence quality and missing fields
- safety, originality, copyright, licensed-character, product-claim, music-rights, child-privacy, and coverage risks
- actions to decide, note, save, brief, and report

Observed, calculated, interpreted, and human-reviewed states remain visually distinct.

## Opportunities and briefs

Saved opportunities remain linked to the source signal. Briefs contain the source mechanism, evidence, audience need, original hook and structure, creator type, complexity, decision window, non-copy guidance, safety, rights, and evidence limitations.

Originality and safety confirmations start unchecked. A brief cannot be marked review-ready until the required confirmations are completed by the user.

The user must explicitly choose inclusion in a report. “Save opportunity” leaves
`include_in_report=false`; “Add to report” sets it true. Report generation may also pass an explicit
list of owned opportunity IDs. Scores and recommendations never select creative opportunities on the
user's behalf.

## Reports

Report reading order:

1. Executive summary
2. Act now
3. Monitor
4. Avoid or hold
5. Emerging toy categories
6. Emerging creators
7. Emerging hashtags
8. Content mechanisms
9. Creative opportunities
10. Safety and originality
11. Evidence and limitations
12. Methodology

CSV, XLSX, HTML, and raw data are secondary analyst exports.

Reports are owner-scoped by migration `0006_user_scoped_reports`; list, review and export operations
cannot read another authenticated user's report. The frontend uses a per-browser HTTP-only JWT
session and never auto-authenticates visitors as the seeded administrator. This boundary still does
not provide tenant or client-workspace isolation.

## Watchlist and monitoring limitations

The toy Track page currently reads seeded stored watchlist definitions. The toy API has no watchlist
mutation endpoints and its read query is not yet user-filtered, so this surface is single-user demo
configuration. The older `/watchlists` editor stores choices in browser local storage only; those
choices do not modify backend taxonomy, collection inputs or provider scheduling.

The monitoring policy and `toy-refresh --due [--limit N]` command do not create background work. The
read-only plan excludes demo/mixed evidence and is bounded by the configured provider URL limit plus
a hard maximum of 20. There is no scheduler, queue, automatic refresh or live alert UI. Only an
administrator's separately reviewed and explicitly confirmed provider request may refresh selected
canonical video URLs.

## Brand system

- Deep Navy `#0B1220`
- Primary Ink `#111827`
- Scope Teal `#0F766E`
- Signal Teal `#14B8A6`
- Opportunity Indigo `#4F46E5`
- Canvas `#F7F8FA`
- White `#FFFFFF`
- Border Grey `#D8DEE8`

Inter Tight is used for headings, Inter for interface/body copy, and IBM Plex Mono for analytical values. The application is light-mode first, uses borders before shadows, an 8px default radius, restrained color, and approved exported SignalScope logo assets.

## Accessibility and responsive rules

- WCAG 2.2 AA target
- semantic landmarks, skip link, logical headings, and visible focus
- keyboard-operable navigation, tabs, drawers, dialogs, and disclosures
- focus trap, Escape close, and focus return for modal surfaces
- status icon plus text; never color only
- reduced-motion support
- accessible table captions and column headers
- minimum 44px interactive targets
- no interactive role on table rows containing nested links or controls

At 390px the product keeps conclusion, lifecycle, recommendation, confidence, freshness, main limitation, safety, Save, Note, and Add to report visible. Detailed evidence is progressively disclosed. Page-level horizontal scrolling is not permitted.
