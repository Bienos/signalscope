import Link from 'next/link';
import {DataModeBanner} from '../../components/toys/DataModeBanner';
import {SignalCard} from '../../components/toys/SignalCard';
import {SignalTable} from '../../components/toys/SignalTable';
import {getToySignals} from '../../lib/toys/api';
import type {ToySignal, TrendLifecycle} from '../../lib/toys/types';

export const metadata = {title: 'Discover toy signals'};
const lifecycles: TrendLifecycle[] = ['Emerging', 'Accelerating', 'Breakout', 'Viral', 'Saturated', 'Declining', 'Recurring', 'Insufficient evidence'];

export default async function Page({searchParams}: {searchParams: Promise<Record<string, string | undefined>>}) {
  const params = await searchParams;
  const collection = await getToySignals();
  const view = params.view === 'analyst' ? 'analyst' : 'decision';
  const q = (params.q || '').toLowerCase();
  const rows = collection.items.filter((signal) => {
    const creatorTypes = signal.relationships?.creator_types || [];
    return (!params.lifecycle || signal.lifecycle === params.lifecycle)
      && (!params.market || signal.markets.includes(params.market))
      && (!params.language || signal.languages.includes(params.language))
      && (!params.category || signal.category === params.category)
      && (!params.mechanism || signal.mechanism === params.mechanism)
      && (!params.decision || signal.recommendation === params.decision)
      && (!params.confidence || signal.confidence === params.confidence)
      && (!params.safety || signal.safety_state === params.safety)
      && (!params.freshness || signal.freshness_status === params.freshness)
      && (!params.creator_type || creatorTypes.includes(params.creator_type))
      && (!q || `${signal.title} ${signal.conclusion} ${signal.category} ${signal.mechanism}`.toLowerCase().includes(q));
  });
  const categories = unique(collection.items.map((item) => item.category));
  const mechanisms = unique(collection.items.map((item) => item.mechanism));
  const creators = unique(collection.items.flatMap((item) => item.relationships?.creator_types || []));

  return <>
    <header className="pagehead"><div><div className="eyebrow">Toy signal discovery</div><h1 className="title">Discover</h1><p className="subtitle">Start with the decision conclusion, then inspect the posts, snapshots and limitations behind it.</p></div><Link className="action" href="/track">Open tracked entities</Link></header>
    <DataModeBanner mode={collection.mode} modeLabel={collection.mode_label} coverage={collection.coverage} provider={collection.provider} lastObservation={collection.last_observation}/>
    <nav className="lifecycletabs" aria-label="Lifecycle filters">
      <Link className={!params.lifecycle ? 'active' : ''} href="/discover">All</Link>
      {lifecycles.map((item) => <Link className={params.lifecycle === item ? 'active' : ''} href={`/discover?lifecycle=${encodeURIComponent(item)}`} key={item}>{item}</Link>)}
    </nav>
    <form className="discoverfilters" aria-label="Discover toy signals">
      {params.lifecycle && <input type="hidden" name="lifecycle" value={params.lifecycle}/>}<input type="hidden" name="view" value={view}/>
      <label>Search<input name="q" defaultValue={params.q || ''} placeholder="Signal, category or mechanism"/></label>
      <label>Market<select name="market" defaultValue={params.market || ''}><option value="">GB + PL</option><option>GB</option><option>PL</option></select></label>
      <label>Language<select name="language" defaultValue={params.language || ''}><option value="">EN + PL</option><option value="en">English</option><option value="pl">Polish</option></select></label>
      <label>Category<select name="category" defaultValue={params.category || ''}><option value="">All toy categories</option>{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label>Mechanism<select name="mechanism" defaultValue={params.mechanism || ''}><option value="">All mechanisms</option>{mechanisms.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label>Decision<select name="decision" defaultValue={params.decision || ''}><option value="">All decisions</option><option>Act</option><option>Monitor</option><option>Avoid</option></select></label>
      <label>Confidence<select name="confidence" defaultValue={params.confidence || ''}><option value="">All confidence</option><option>High</option><option>Medium</option><option>Low</option></select></label>
      <label>Safety<select name="safety" defaultValue={params.safety || ''}><option value="">All safety states</option><option>Clear</option><option>Review</option><option>Hold</option></select></label>
      <label>Freshness<select name="freshness" defaultValue={params.freshness || ''}><option value="">All freshness</option><option>Fresh</option><option>Stale</option><option>Unavailable</option></select></label>
      <label>Creator type<select name="creator_type" defaultValue={params.creator_type || ''}><option value="">All observed types</option>{creators.map((item) => <option key={item}>{item}</option>)}</select></label>
      <div className="filteractions"><button className="action" type="submit">Apply filters</button><Link href="/discover">Reset</Link></div>
    </form>
    <div className="discovertoolbar"><p><b>{rows.length}</b> of {collection.total} toy signals</p><div role="group" aria-label="Display mode"><Link className={view === 'decision' ? 'active' : ''} href={withParams(params, 'decision')}>Decision view</Link><Link className={view === 'analyst' ? 'active' : ''} href={withParams(params, 'analyst')}>Analyst table</Link></div></div>
    {view === 'decision'
      ? <div className="signalcardgrid">{rows.map((signal: ToySignal) => <SignalCard signal={signal} key={signal.id}/>)}</div>
      : <SignalTable signals={rows}/>
    }
  </>;
}

function unique(values: string[]) { return Array.from(new Set(values)).sort(); }
function withParams(params: Record<string, string | undefined>, view: string) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => { if (value && key !== 'view') query.set(key, value); });
  query.set('view', view);
  return `/discover?${query.toString()}`;
}
