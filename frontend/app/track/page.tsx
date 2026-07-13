import Link from 'next/link';
import {DataModeBanner} from '../../components/toys/DataModeBanner';
import {StatusPill} from '../../components/toys/StatusPill';
import {getToyCreators, getToyHashtags, getToySounds, getToyWatchlists} from '../../lib/toys/api';
import {displayCompactMetric, displayDateTime, displayMetric} from '../../lib/toys/formatters';

export const metadata = {title: 'Track toy-market entities'};
const tabs = ['watchlists', 'creators', 'hashtags', 'sounds'] as const;
type Tab = typeof tabs[number];

export default async function Page({searchParams}: {searchParams: Promise<{tab?: string}>}) {
  const [{tab: requested}, watchlists, creators, hashtags, sounds] = await Promise.all([
    searchParams,
    getToyWatchlists(),
    getToyCreators(),
    getToyHashtags(),
    getToySounds(),
  ]);
  const tab: Tab = tabs.includes(requested as Tab) ? requested as Tab : 'watchlists';
  const source = tab === 'creators' ? creators : tab === 'hashtags' ? hashtags : tab === 'sounds' ? sounds : watchlists;

  return <>
    <header className="pagehead"><div><div className="eyebrow">Supporting research entities</div><h1 className="title">Track</h1><p className="subtitle">Follow the watchlists, creators, hashtags and sounds that explain movement in toy-market signals.</p></div><Link className="action" href="/discover">Discover signals</Link></header>
    <DataModeBanner mode={source.mode} modeLabel={source.mode_label} coverage={source.coverage} provider={source.provider} lastObservation={source.last_observation}/>
    <nav className="tracktabs" aria-label="Track areas">{tabs.map((item) => <Link className={tab === item ? 'active' : ''} aria-current={tab === item ? 'page' : undefined} href={`/track?tab=${item}`} key={item}>{item[0].toUpperCase() + item.slice(1)}</Link>)}</nav>
    {tab === 'watchlists' && <section><div className="sectionhead"><div><span className="eyebrow">Configured scope</span><h2>Watchlists</h2></div><small>Collection settings are managed in Workspace.</small></div><div className="watchlistgrid">{watchlists.items.map((item) => <article className="panel trackcard" key={item.id}><header><StatusPill value={item.data_status}/><b>{item.signals_requiring_attention} need attention</b></header><h2>{item.name}</h2><p>{item.objective}</p><dl><div><dt>Categories</dt><dd>{item.categories.join(' · ')}</dd></div><div><dt>Markets</dt><dd>{item.markets.join(' · ')}</dd></div><div><dt>Languages</dt><dd>{item.languages.join(' · ')}</dd></div><div><dt>Last reviewed</dt><dd>{displayDateTime(item.last_reviewed)}</dd></div></dl><aside><b>Last important change</b>{item.last_important_change}</aside></article>)}</div></section>}
    {tab === 'creators' && <section><div className="sectionhead"><div><span className="eyebrow">Observed public profiles</span><h2>Creators</h2></div><small>Account market is not audience geography.</small></div><div className="entitycards">{creators.items.map((item) => <article className="panel entitycard" key={item.id}><header><span className="lifecyclepill">{item.creator_type}</span><span>{item.market}</span></header><h2>@{item.username}</h2><p>{item.display_name}</p><dl><div><dt>Followers</dt><dd>{displayCompactMetric(item.followers)}</dd></div><div><dt>Recent posts</dt><dd>{item.recent_post_count}</dd></div><div><dt>Baseline velocity</dt><dd>{displayCompactMetric(item.baseline_velocity)}{item.baseline_velocity !== null ? '/hr' : ''}</dd></div><div><dt>Evidence</dt><dd>{item.evidence_quality}</dd></div></dl><small>{item.toy_categories.join(' · ')}</small>{item.breakout_signal && <p><b>Current breakout:</b> {item.breakout_signal}</p>}</article>)}</div></section>}
    {tab === 'hashtags' && <section><div className="sectionhead"><div><span className="eyebrow">Toy-post adoption</span><h2>Hashtags</h2></div><small>Observed sample, not accumulated platform volume.</small></div><div className="tablewrap"><table className="table entitytable"><caption>Toy hashtag adoption and saturation</caption><thead><tr><th>Hashtag</th><th>Market</th><th>Posts</th><th>Creators</th><th>Creator growth</th><th>Lifecycle</th><th>Saturation</th><th>Freshness</th></tr></thead><tbody>{hashtags.items.map((item) => <tr key={item.id}><td data-label="Hashtag"><b>{item.name.startsWith('#') ? item.name : `#${item.name}`}</b><small>{item.categories.join(' · ')}</small></td><td data-label="Market">{item.market}</td><td data-label="Posts" className="numeric">{item.observed_posts}</td><td data-label="Creators" className="numeric">{item.unique_creators}</td><td data-label="Growth" className="numeric">{displayMetric(item.creator_growth, item.creator_growth !== null ? '%' : '')}</td><td data-label="Lifecycle">{item.lifecycle}</td><td data-label="Saturation" className="numeric">{displayMetric(item.saturation, item.saturation !== null ? '%' : '')}</td><td data-label="Freshness">{displayDateTime(item.freshness_at)}</td></tr>)}</tbody></table></div></section>}
    {tab === 'sounds' && <section><div className="sectionhead"><div><span className="eyebrow">Sound spread through toy content</span><h2>Sounds</h2></div><small>Rights status is not music clearance.</small></div><div className="entitycards">{sounds.items.map((item) => <article className="panel entitycard" key={item.id}><header><span className="lifecyclepill">{item.lifecycle}</span><span className="statuspill tone-warning">Rights: {item.rights_status}</span></header><h2>{item.title}</h2><p>{item.categories.join(' · ')}</p><dl><div><dt>Toy posts</dt><dd>{item.toy_post_adoption}</dd></div><div><dt>Creators</dt><dd>{item.independent_creators}</dd></div><div><dt>Momentum</dt><dd>{displayMetric(item.post_momentum, item.post_momentum !== null ? '×' : '')}</dd></div><div><dt>Freshness</dt><dd>{displayDateTime(item.freshness_at)}</dd></div></dl></article>)}</div></section>}
  </>;
}
