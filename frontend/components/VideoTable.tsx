'use client';

import {Fragment, useMemo, useState} from 'react';
import Link from 'next/link';
import {getPlan} from '../lib/commercial';
import {displayCompactMetric, displayDateTime, displayMetric} from '../lib/toys/formatters';
import {useCommercial} from './CommercialProvider';

type V = {id: number; url: string; creator: string; caption: string; market: string; language: string; category: string; score: number | null; score_type?: 'AVS' | 'EVS'; score_context?: string; growth: number | null; velocity: number | null; acceleration?: number | null; confidence: string; safety: string; reason: string; evidence_type?: string; current_views?: number | null; video_age_hours?: number | null; snapshot_count?: number; provider_freshness?: string | null; hashtags?: string[]; copyright_warning?: string};
const confidenceIcon = (value: string) => value.toLowerCase() === 'high' ? '●' : value.toLowerCase() === 'medium' ? '◐' : '○';
const sortable = (value: number | null | undefined) => value ?? Number.NEGATIVE_INFINITY;

export function VideoTable({rows, mode = 'all'}: {rows: V[]; mode?: 'viral' | 'emerging' | 'all'}) {
  const {plan} = useCommercial();
  const resultLimit = getPlan(plan).quotas.resultsPerView ?? rows.length;
  const [sort, setSort] = useState<'score' | 'velocity' | 'acceleration' | 'freshness'>('score');
  const [open, setOpen] = useState<number | null>(null);
  const sorted = useMemo(() => [...rows].sort((a, b) => sort === 'velocity'
    ? sortable(b.velocity) - sortable(a.velocity)
    : sort === 'acceleration'
      ? sortable(b.acceleration) - sortable(a.acceleration)
      : sort === 'freshness'
        ? String(b.provider_freshness || '').localeCompare(String(a.provider_freshness || ''))
        : sortable(b.score) - sortable(a.score)), [rows, sort]);

  return <>
    <div className="evidence-strip"><span><b>DEMO TOY DATA</b> · legacy post evidence view</span><label>Sort by <select value={sort} onChange={(event) => setSort(event.target.value as typeof sort)}><option value="score">Score</option><option value="velocity">Velocity</option><option value="acceleration">Acceleration</option><option value="freshness">Freshness</option></select></label></div>
    <div className="tablewrap"><table className="table signal-table"><caption>Ranked observed video evidence. Use the button in each row for details.</caption><thead><tr><th>Rank</th><th>Post</th><th>Creator</th><th>Age</th><th>Market</th><th>Velocity</th><th>Acceleration</th><th>Score</th><th>Confidence</th><th>Safety</th><th>Freshness</th></tr></thead><tbody>{sorted.slice(0, resultLimit).map((video, index) => <Fragment key={video.id}><tr><td><b>#{index + 1}</b></td><td><a className="link" target="_blank" rel="noreferrer" href={video.url}>{video.caption}</a><div className="label">{video.category} · {video.reason}</div><button className="rowdetails" type="button" aria-expanded={open === video.id} aria-controls={`video-evidence-${video.id}`} onClick={() => setOpen((current) => current === video.id ? null : video.id)}>{open === video.id ? 'Hide evidence' : 'Show evidence'}</button></td><td>@{video.creator}</td><td>{video.video_age_hours == null ? 'Unavailable' : `${Math.round(video.video_age_hours)}h`}</td><td>{video.market}<div className="label">{video.language}</div></td><td><b>{displayCompactMetric(video.velocity)}</b><div className="label">views/hour</div></td><td>{displayMetric(video.acceleration, video.acceleration != null ? '×' : '')}</td><td><span className="score">{video.score_type || (mode === 'emerging' ? 'EVS' : 'AVS')} {displayMetric(video.score)}</span><div className="label">{video.score_context}</div></td><td><span className="confidence">{confidenceIcon(video.confidence)} {video.confidence}</span><div className="label">{video.snapshot_count ?? 0} observations</div></td><td><span className={video.safety === 'clear' ? 'status-ok' : 'status-review'}>{video.safety === 'clear' ? '✓ Clear' : '! Review'}</span></td><td>{displayDateTime(video.provider_freshness)}</td></tr>{open === video.id && <tr className="detailrow" id={`video-evidence-${video.id}`}><td colSpan={11}><div className="detailgrid"><section><h3>Evidence</h3><p>{displayCompactMetric(video.current_views)} current views · {displayCompactMetric(video.growth)} growth</p><p>{video.snapshot_count ?? 0} snapshots · {video.evidence_type || 'Demo evidence'}</p></section><section><h3>Context</h3><p>{video.hashtags?.map((tag) => `#${tag}`).join(' · ') || 'No hashtags supplied'}</p><p>Cohort: {video.market} · {video.language} · {video.category}</p></section><section><h3>Responsible adaptation</h3><p>Use the broad mechanism and audience need. Do not copy protected execution.</p><p>{video.copyright_warning || 'Rights status unavailable.'}</p></section></div></td></tr>}</Fragment>)}</tbody></table></div>
    {sorted.length > resultLimit && <div className="upgradebar"><b>{sorted.length - resultLimit} more results are hidden in this entitlement preview.</b><Link href="/pricing">Compare plans →</Link></div>}
  </>;
}
