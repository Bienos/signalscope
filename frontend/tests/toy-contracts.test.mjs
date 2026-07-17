import assert from 'node:assert/strict';
import {access, readFile} from 'node:fs/promises';
import test from 'node:test';

const fixtureUrl = new URL('../lib/toys/demo-fixtures.json', import.meta.url);
const fixture = JSON.parse(await readFile(fixtureUrl, 'utf8'));
const source = async (path) => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const requiredSignalFields = [
  'id', 'title', 'conclusion', 'category', 'mechanism', 'lifecycle', 'recommendation',
  'markets', 'languages', 'opportunity_score', 'confidence', 'freshness_at',
  'freshness_status', 'saturation', 'velocity', 'acceleration', 'creator_spread',
  'post_count', 'snapshot_count', 'why_it_matters', 'main_limitation', 'decision_window',
  'safety_state', 'score_version', 'demo',
];

test('demo fixtures cover the decision workflow and lifecycle states', () => {
  assert.ok(fixture.signals.length >= 12);
  assert.ok(fixture.videos.length >= 30 && fixture.videos.length <= 50);
  assert.ok(fixture.creators.length >= 12 && fixture.creators.length <= 20);
  assert.ok(fixture.hashtags.length >= 20);
  assert.ok(fixture.sounds.length >= 8);
  assert.ok(fixture.opportunities.length >= 3);
  assert.ok(fixture.reports.length >= 2);
  assert.deepEqual(new Set(fixture.signals.map((signal) => signal.recommendation)), new Set(['Act', 'Monitor', 'Avoid']));
  for (const lifecycle of ['Insufficient evidence', 'Emerging', 'Accelerating', 'Breakout', 'Viral', 'Saturated', 'Declining', 'Recurring']) {
    assert.ok(fixture.signals.some((signal) => signal.lifecycle === lifecycle), `missing lifecycle: ${lifecycle}`);
  }
});

test('every toy signal satisfies the provider-independent core contract', () => {
  for (const signal of fixture.signals) {
    for (const field of requiredSignalFields) assert.ok(Object.hasOwn(signal, field), `${signal.id} missing ${field}`);
    assert.equal(signal.demo, true);
    assert.ok(signal.markets.every((market) => ['GB', 'PL'].includes(market)));
    assert.ok(signal.languages.every((language) => ['en', 'pl'].includes(language)));
  }
});

test('insufficient evidence preserves unavailable metrics as null', () => {
  const insufficient = fixture.signals.find((signal) => signal.lifecycle === 'Insufficient evidence');
  assert.ok(insufficient);
  assert.equal(insufficient.snapshot_count, 1);
  assert.equal(insufficient.velocity, null);
  assert.equal(insufficient.acceleration, null);
  assert.equal(insufficient.opportunity_score, null);
});

test('fixtures retain source links and explicit rights uncertainty', () => {
  assert.ok(fixture.opportunities.every((item) => fixture.signals.some((signal) => signal.id === item.signal_id)));
  assert.ok(fixture.sounds.every((sound) => sound.rights_status === 'Unknown'));
  assert.match(JSON.stringify(fixture), /Synthetic demo observation|Synthetic demo data/);
});

test('raw Apify field names do not leak into the frontend fixture contract', () => {
  const payload = JSON.stringify(fixture);
  for (const rawName of ['playCount', 'diggCount', 'authorMeta', 'musicMeta']) {
    assert.equal(payload.includes(rawName), false, `raw provider field leaked: ${rawName}`);
  }
});

test('primary navigation and all lifecycle filters are represented', async () => {
  const [nav, discover] = await Promise.all([
    source('components/Nav.tsx'),
    source('app/discover/page.tsx'),
  ]);
  for (const route of ['/dashboard', '/discover', '/track', '/opportunities', '/reports', '/workspace']) {
    assert.match(nav, new RegExp(route.replace('/', '\\/')));
  }
  assert.match(discover, /'Recurring'/);
  assert.match(discover, /aria-label="Lifecycle filters"/);
});

test('decision notes and report selection use the backend contracts', async () => {
  const [workflow, report, dashboard] = await Promise.all([
    source('components/toys/SignalWorkflowActions.tsx'),
    source('components/toys/ToyReportActions.tsx'),
    source('app/dashboard/page.tsx'),
  ]);
  assert.match(workflow, /analyst_note: note/);
  assert.match(workflow, /include_in_report: true/);
  assert.doesNotMatch(report, /source: 'selected_opportunities'/);
  assert.doesNotMatch(dashboard, /<SignalCard signal=\{signal\} compact/);
});

test('demo fallback is explicit and production requests use a user session', async () => {
  const [api, session, proxy, exportProxy] = await Promise.all([
    source('app/lib.ts'),
    source('lib/server-session.ts'),
    source('app/api/toys/[...path]/route.ts'),
    source('app/api/reports/[id]/export/[format]/route.ts'),
  ]);
  assert.match(session, /SIGNALSCOPE_DEMO_MODE/);
  assert.match(api, /sessionCookieName/);
  assert.match(proxy, /requestAuthorization/);
  assert.match(exportProxy, /requestAuthorization/);
  for (const content of [api, session, proxy, exportProxy]) {
    assert.doesNotMatch(content, /RadarDemo!2026|admin@viralradar\.local/);
  }
});

test('responsive layouts expose mobile cards and reduced-motion behavior', async () => {
  const styles = await source('app/toy-platform.css');
  assert.match(styles, /@media \(max-width: 430px\)/);
  assert.match(styles, /\.toysignaltable tr/);
  assert.match(styles, /prefers-reduced-motion/);
  assert.match(styles, /:focus-visible/);
});

test('approved brand assets are used consistently across light and dark surfaces', async () => {
  const [brandLogo, nav, landing, footer, publicHeader, appFrame, layout, manifest, schema, dockerfile] = await Promise.all([
    source('components/BrandLogo.tsx'),
    source('components/Nav.tsx'),
    source('components/LandingPage.tsx'),
    source('components/SiteFooter.tsx'),
    source('components/PublicHeader.tsx'),
    source('components/AppFrame.tsx'),
    source('app/layout.tsx'),
    source('app/manifest.ts'),
    source('lib/structured-data.ts'),
    source('Dockerfile'),
  ]);

  for (const asset of [
    'public/brand/signalscope-wordmark-on-light.png',
    'public/brand/signalscope-wordmark-on-dark.png',
    'public/brand/signalscope-mark-teal.png',
  ]) await access(new URL(`../${asset}`, import.meta.url));

  assert.match(brandLogo, /signalscope-wordmark-on-dark\.png/);
  assert.match(brandLogo, /signalscope-wordmark-on-light\.png/);
  assert.match(nav, /variant="on-dark"/);
  assert.match(landing, /variant="on-dark"/);
  assert.match(footer, /variant="on-dark"/);
  assert.match(publicHeader, /variant="on-light"/);
  assert.match(appFrame, /<PublicHeader\/>/);
  assert.match(layout, /signalscope-mark-teal\.png/);
  assert.match(manifest, /signalscope-mark-teal\.png/);
  assert.match(schema, /signalscope-mark-teal\.png/);
  assert.match(dockerfile, /COPY --from=build \/app\/public \.\/public/);
});

test('public positioning is category-flexible while the dashboard remains toys-only', async () => {
  const [landing, homeMetadata, dashboard, seo] = await Promise.all([
    source('components/LandingPage.tsx'),
    source('app/page.tsx'),
    source('app/dashboard/page.tsx'),
    source('lib/seo-content.ts'),
  ]);
  assert.match(landing, /Short-form intelligence for agencies and consumer teams/);
  assert.match(landing, /multi-client research/i);
  assert.match(landing, /Current product preview: toys and family/);
  assert.doesNotMatch(landing, /LanguageSelector/);
  assert.doesNotMatch(landing, />Demo</);
  assert.match(homeMetadata, /Short-form trend intelligence for agencies and consumer teams/);
  assert.match(dashboard, /Toy Market Intelligence/);
  assert.match(dashboard, /Toys &amp; family/);
  assert.match(dashboard, /More categories/);
  assert.match(dashboard, /Coming soon/);
  assert.match(seo, /current working dashboard demonstrates toys/);
});
