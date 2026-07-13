import Link from 'next/link';
import {DataModeBanner} from '../../components/toys/DataModeBanner';
import {SignalCard} from '../../components/toys/SignalCard';
import {getToyOverview} from '../../lib/toys/api';
import {displayDateTime} from '../../lib/toys/formatters';
import type {ToySignal} from '../../lib/toys/types';

export const metadata = {title: 'Today · Toy market intelligence'};

function matches(signal: ToySignal, market: string, language: string, category: string) {
  return (!market || signal.markets.includes(market))
    && (!language || signal.languages.includes(language))
    && (!category || signal.category === category);
}

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const [overview, params] = await Promise.all([getToyOverview(), searchParams]);
  const market = params.market || '';
  const language = params.language || '';
  const category = params.category || '';
  const queue = {
    act: overview.decision_queue.act.filter((signal) => matches(signal, market, language, category)),
    monitor: overview.decision_queue.monitor.filter((signal) => matches(signal, market, language, category)),
    avoid: overview.decision_queue.avoid.filter((signal) => matches(signal, market, language, category)),
  };
  const categories = Array.from(new Set(Object.values(overview.decision_queue).flat().map((signal) => signal.category))).sort();

  return <>
    <header className="pagehead toybriefhead">
      <div><div className="eyebrow">Today · Europe/Warsaw</div><h1 className="title">Toy Market Intelligence</h1><p className="subtitle">What changed, why it matters to the toy market, and what the team should do next.</p></div>
      <Link className="action" href="/reports">Prepare decision report</Link>
    </header>
    <form className="scopebar" aria-label="Toy brief filters">
      <label>Market<select name="market" defaultValue={market}><option value="">GB + PL</option><option value="GB">GB</option><option value="PL">PL</option></select></label>
      <label>Language<select name="language" defaultValue={language}><option value="">English + Polish</option><option value="en">English</option><option value="pl">Polish</option></select></label>
      <label>Product category<select name="category" defaultValue={category}><option value="">All toy categories</option>{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label>Date range<select name="range" defaultValue={params.range || '24h'}><option value="24h">Last 24 hours</option><option value="7d">Last 7 days</option></select></label>
      <button className="action" type="submit">Apply</button>
    </form>
    <DataModeBanner
      mode={overview.mode}
      modeLabel={overview.mode_label}
      coverage={overview.coverage}
      provider={overview.provider.name}
      lastObservation={overview.provider.last_observation}
      freshness={overview.provider.freshness_status}
    />

    <section className="briefsection" aria-labelledby="changes-title">
      <div className="sectionhead"><div><span className="eyebrow">Since your last review</span><h2 id="changes-title">The important changes</h2></div><small>Last observation {displayDateTime(overview.provider.last_observation)}</small></div>
      <div className="changegrid">{overview.since_last_review.map((item) => <article key={item.type}><strong>{item.count}</strong><h3>{item.label}</h3><p>{item.detail}</p></article>)}</div>
    </section>

    <section className="briefsection" aria-labelledby="queue-title">
      <div className="sectionhead"><div><span className="eyebrow">Decision queue</span><h2 id="queue-title">Act, monitor or avoid</h2></div><Link href="/opportunities">Open all decisions →</Link></div>
      <div className="decisioncolumns">
        {(['act', 'monitor', 'avoid'] as const).map((group) => <section key={group} aria-labelledby={`${group}-title`}>
          <header><h3 id={`${group}-title`}>{group === 'act' ? 'Act' : group === 'monitor' ? 'Monitor' : 'Avoid or hold'}</h3><span>{queue[group].length}</span></header>
          {queue[group].slice(0, 2).map((signal) => <SignalCard signal={signal} key={signal.id}/>)}
          {!queue[group].length && <div className="empty compactempty">No matching {group} signals.</div>}
        </section>)}
      </div>
    </section>

    <section className="briefsection" aria-labelledby="pulse-title">
      <div className="sectionhead"><div><span className="eyebrow">Market pulse</span><h2 id="pulse-title">Where adoption is moving</h2></div><Link href="/discover">Explore evidence →</Link></div>
      <div className="pulsegrid">
        <Pulse title="Toy categories" items={overview.market_pulse.categories}/>
        <Pulse title="Hashtags" items={overview.market_pulse.hashtags}/>
        <Pulse title="Creators" items={overview.market_pulse.creators}/>
        <Pulse title="Content mechanisms" items={overview.market_pulse.mechanisms}/>
        <Pulse title="Sounds in toy content" items={overview.market_pulse.sounds}/>
      </div>
    </section>

    <section className="reportreadiness" aria-labelledby="readiness-title">
      <div><span className="eyebrow">Report readiness</span><h2 id="readiness-title">{overview.report_readiness.status}</h2><p>Complete analyst notes and resolve review items before sharing externally.</p></div>
      <dl><div><dt>Selected</dt><dd>{overview.report_readiness.opportunities_selected}</dd></div><div><dt>Notes complete</dt><dd>{overview.report_readiness.notes_completed}</dd></div><div><dt>Awaiting review</dt><dd>{overview.report_readiness.awaiting_review}</dd></div></dl>
      <Link className="action" href="/reports">Continue report</Link>
    </section>
  </>;
}

function Pulse({title, items}: {title: string; items: string[]}) {
  return <article><h3>{title}</h3><ol>{items.map((item) => <li key={item}>{item}</li>)}</ol></article>;
}
