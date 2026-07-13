import Link from 'next/link';
import {notFound} from 'next/navigation';
import {DataModeBanner} from '../../../components/toys/DataModeBanner';
import {SignalWorkflowActions} from '../../../components/toys/SignalWorkflowActions';
import {ConfidencePill, StatusPill} from '../../../components/toys/StatusPill';
import {getToySignal} from '../../../lib/toys/api';
import {displayCompactMetric, displayDateTime, displayMetric} from '../../../lib/toys/formatters';

export async function generateMetadata({params}: {params: Promise<{id: string}>}) {
  const signal = await getToySignal((await params).id);
  return {title: signal ? `${signal.title} · Toy signal` : 'Toy signal'};
}

export default async function Page({params}: {params: Promise<{id: string}>}) {
  const signal = await getToySignal((await params).id);
  if (!signal) notFound();
  const quality = signal.quality;
  const relationships = signal.relationships;
  const risks = signal.risks;
  return <>
    <Link className="backlink" href="/discover">← Back to Discover</Link>
    <DataModeBanner mode={signal.demo ? 'demo' : 'live'} modeLabel={signal.demo ? 'DEMO TOY DATA' : 'LIVE PROVIDER DATA'} coverage={quality?.coverage_limitations.join(' · ') || signal.main_limitation} provider={quality?.provider} lastObservation={signal.freshness_at} freshness={signal.freshness_status}/>
    <header className="signaldetailhead">
      <div className="pillrow"><StatusPill value={signal.recommendation}/><span className="lifecyclepill">{signal.lifecycle}</span><ConfidencePill value={signal.confidence}/><StatusPill value={signal.freshness_status}/></div>
      <h1 className="title">{signal.title}</h1><p className="detailconclusion">{signal.conclusion}</p>
      <div className="signalcontext"><span>{signal.category}</span><span>{signal.mechanism}</span><span>{signal.markets.join(' · ')}</span><span>{signal.languages.join(' · ')}</span></div>
      <p><b>Decision window:</b> {signal.decision_window}</p>
    </header>
    <section className="detailsection" aria-labelledby="moving-title"><div className="sectionhead"><div><span className="eyebrow">Interpretation</span><h2 id="moving-title">Why it is moving</h2></div><small>{signal.score_version}</small></div><p className="detaillead">{signal.why_it_matters}</p><div className="detailmetrics"><Metric label="Opportunity score" value={signal.opportunity_score === null ? 'Unavailable' : `${signal.opportunity_score}`}/><Metric label="Velocity" value={`${displayCompactMetric(signal.velocity)}${signal.velocity !== null ? '/hr' : ''}`}/><Metric label="Acceleration" value={displayMetric(signal.acceleration, signal.acceleration !== null ? '×' : '')}/><Metric label="Creator spread" value={`${signal.creator_spread}`}/><Metric label="Posts" value={`${signal.post_count}`}/><Metric label="Saturation" value={displayMetric(signal.saturation, signal.saturation !== null ? '%' : '')}/></div></section>
    <section className="detailsection" aria-labelledby="evidence-title"><div className="sectionhead"><div><span className="eyebrow">Observed support</span><h2 id="evidence-title">Representative evidence</h2></div><small>{signal.snapshot_count} snapshots</small></div>{signal.evidence?.length ? <div className="tablewrap"><table className="table evidencetable"><caption>Representative public post evidence</caption><thead><tr><th>Post</th><th>Creator</th><th>Published</th><th>Views</th><th>Growth</th><th>Velocity</th><th>Market</th><th>Source</th></tr></thead><tbody>{signal.evidence.map((item) => <tr key={item.id}><td data-label="Post"><b>{item.caption}</b><small>{item.hashtags.map((tag) => `#${tag}`).join(' · ')}</small></td><td data-label="Creator">@{item.creator}<small>{item.creator_type}</small></td><td data-label="Published">{displayDateTime(item.published_at)}</td><td data-label="Views" className="numeric">{displayCompactMetric(item.views)}</td><td data-label="Growth" className="numeric">{displayCompactMetric(item.growth)}</td><td data-label="Velocity" className="numeric">{displayCompactMetric(item.velocity)}</td><td data-label="Market">{item.market}</td><td data-label="Source"><a href={item.canonical_url} target="_blank" rel="noreferrer">Open TikTok ↗</a><small>{item.evidence_type}</small></td></tr>)}</tbody></table></div> : <div className="empty"><b>No representative posts are available.</b><p>The signal conclusion remains visible, but source-level inspection is unavailable.</p></div>}</section>
    <div className="detailtwocolumn">
      <section className="panel"><span className="eyebrow">Relationships</span><h2>How the signal connects</h2><DetailList title="Hashtags" values={relationships?.hashtags}/><DetailList title="Sounds" values={relationships?.sounds}/><DetailList title="Creator types" values={relationships?.creator_types}/><DetailList title="Market differences" values={relationships?.market_notes}/></section>
      <section className="panel"><span className="eyebrow">Evidence quality</span><h2>Why confidence is {signal.confidence.toLowerCase()}</h2><p>{quality?.confidence_explanation || signal.main_limitation}</p><dl className="qualitylist"><div><dt>Snapshots</dt><dd>{quality?.snapshot_count ?? signal.snapshot_count}</dd></div><div><dt>Cohort</dt><dd>{quality?.cohort_size ?? signal.post_count}</dd></div><div><dt>First observed</dt><dd>{displayDateTime(quality?.first_observed)}</dd></div><div><dt>Last observed</dt><dd>{displayDateTime(quality?.last_observed || signal.freshness_at)}</dd></div><div><dt>Missing fields</dt><dd>{quality?.missing_fields.join(' · ') || 'None reported'}</dd></div></dl></section>
    </div>
    <section className="risksection"><span className="eyebrow">Risk review</span><h2>Safety, rights and evidence limitations</h2><div className="riskgrid"><Risk title="Toy safety" values={risks?.safety}/><Risk title="Copyright and licensed characters" values={risks?.copyright}/><Risk title="Product claims" values={risks?.product_claims}/><Risk title="Child privacy" values={risks?.child_privacy}/><Risk title="Music rights" values={[risks?.music_rights || 'Unknown — verify before commercial use.']}/><Risk title="Evidence limitations" values={risks?.evidence_limitations || [signal.main_limitation]}/></div></section>
    <SignalWorkflowActions signalId={signal.id} current={signal.decision?.recommendation}/>
  </>;
}

function Metric({label, value}: {label: string; value: string}) { return <div><span>{label}</span><strong>{value}</strong></div>; }
function DetailList({title, values}: {title: string; values?: string[]}) { return <div className="detaillist"><h3>{title}</h3><p>{values?.length ? values.join(' · ') : 'Unavailable'}</p></div>; }
function Risk({title, values}: {title: string; values?: string[]}) { return <article><h3>{title}</h3><ul>{values?.length ? values.map((item) => <li key={item}>{item}</li>) : <li>No issue reported in the supplied evidence.</li>}</ul></article>; }
