# SignalScope legal and footer implementation review

Date: 12 July 2026

Status: Draft operational review. Not legal advice. Every public policy requires qualified EU/UK technology and privacy counsel before publication.

## 1. Pages created

- Legal and trust centre
- Terms and Conditions
- Privacy Policy
- Cookie and Local Storage Policy
- Acceptable Use Policy
- Data Sources and Methodology
- AI and Automated Analysis Disclosure
- Copyright, Intellectual Property and Takedown Policy
- Security and Responsible Disclosure
- Pricing, Billing and Cancellation Policy
- Accessibility Statement
- Contact and Legal Information

All pages share breadcrumbs, legal navigation, effective/updated dates, a publication-blocker panel, related-policy links, responsive behavior and print styling.

## 2. Footer links added

The public footer now groups Product, Company, Trust & Transparency, Legal and Follow SignalScope links. Only Dashboard links to the authenticated product; individual research/dashboard links were removed. Its trust area states that SignalScope is independent, is not affiliated with TikTok or ByteDance, covers only a configured monitored sample and currently uses simulated demo data. The authenticated workspace keeps its compact Terms, Privacy, Methodology and Security footer.

X, LinkedIn and Telegram appear as non-interactive “Coming soon” entries because no confirmed profile URL exists. No contact address or cookie-preference control is shown because no confirmed contact route or non-essential tracker exists.

The locale registry includes English, all official EU languages and additional wider-European languages. English is the reference interface. Polish, Spanish and French are selectable beta locales: shared footer, header, dashboard navigation and category-watchlist strings are translated, while substantive untranslated page and legal content falls back to English with a visible notice. All remaining locales are planned and disabled. `signalscope-locale` stores an explicit functional language preference.

The previous Toys & Family paid pack was removed. Toys remains one of twelve centrally configured category choices. The local demo now permits one category watchlist on Free, five on Pro and twenty on Team; additional Free watchlists preserve the draft and show an upgrade explanation.

## 3. Confirmed product facts

- The application is a Next.js frontend and FastAPI/PostgreSQL modular monolith.
- It supports deterministic mock data, validated CSV/JSON imports and a generic authorized REST-provider boundary.
- Core records include accounts, provider runs, creator/post metadata, immutable metric snapshots, scores, mechanisms, reports, report notes and deletion outcomes.
- Passwords are hashed and eight-hour signed bearer tokens protect API access.
- The core model stores official links and metadata, not full video.
- The application distinguishes provider observations, calculations and AI-supported interpretation.
- Billing is not connected; Stripe is only mentioned as a future boundary.
- The AI provider is disabled by default and no live model vendor is identified.
- Local email output exists and SMTP can be configured.
- Current commercial plan switching and gates are a browser-session demonstration, not server-enforced subscriptions.

## 4. Unresolved legal placeholders

- Legal entity, registered address and company number
- Governing law, courts and dispute process
- Privacy, legal, security, accessibility, billing and takedown contacts
- Data protection officer and EU/UK representative analysis
- Lead supervisory authority
- Hosting provider, processing locations and complete subprocessors
- International-transfer mechanisms and assessments
- Payment provider, taxes, renewal, proration, cancellation and refund rules
- Account, reports, notes, logs, billing, backup and deletion-audit retention
- Support and incident response targets
- Liability, warranty, indemnity and consumer-law language

## 5. Claims corrected or qualified

- Policies repeatedly state that monitored coverage is not exhaustive or a complete TikTok ranking.
- Free Preview is described as simulated, not a live free feed.
- Pricing and entitlements are described as hypotheses until checkout or contract approval.
- Alerts, scheduled delivery, shared persistence, billing and provider-backed enforcement are described as planned.
- Scores and AI interpretation are decision support, not predictions, clearance or observed fact.
- Creator account region is not audience geography.
- Metric anomalies are not evidence of fraud.
- Music and content rights remain unknown unless supplied by an authorized source.
- Importing data does not establish a customer’s right or lawful basis to use it.

## 6. Cookies, trackers and browser storage found

- No analytics, advertising or third-party tracking script was found.
- No browser authentication cookie was found in the inspected implementation.
- `signalscope-demo-settings` stores local demo market, language and planned-alert preferences.
- `signalscope-demo-views` stores local saved-view names.
- `signalscope-locale` stores the language explicitly selected by the user.
- `signalscope-category-watchlists` stores category-watchlist demo choices locally in the browser.
- Commercial preview, watchlist and review state is in browser/component state and is not a persistent paid workspace.
- No cookie banner was added because no non-essential tracking was identified. A fresh production scan is required before launch.

## 7. Items for qualified counsel

- Controller/processor roles for provider data, customer imports and reports
- Lawful bases, transparency duties for indirectly collected creator metadata and any disproportionate-effort analysis
- DPIA screening for systematic social-data monitoring, profiling and child-related flags
- Provider licensing for customer display, retention, history, exports and redistribution
- UK/EU representative, DPO and supervisory-authority requirements
- International transfers and vendor data-use terms
- Copyright/takedown, platform terms and music-rights workflow
- Business/consumer classification, renewal, cancellation, taxes and mandatory refund rights
- Liability, indemnity, warranty, dispute, suspension and termination clauses
- Accessibility assessment and any jurisdiction-specific statement requirements

## 8. Verification

- Frontend lint: passed
- TypeScript: passed
- Next.js production build: passed; 33 routes generated, including the legal index and 11 static policy pages
- Backend tests: 8 passed
- Ruff: passed
- MyPy: passed for 22 source files
- Live Docker/browser review: depends on host Docker access; the Codex sandbox cannot access the user’s Docker socket
