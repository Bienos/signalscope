import {api} from '../lib';

export const metadata={title:'Data health'};

export default async function Page(){
 const [o,runs]=await Promise.all([api<any>('/api/overview',{}),api<any[]>('/api/providers',[])]);
 const providerAvailable=Boolean(o.provider_freshness)&&o.provider!=='Unavailable';
 const successfulRuns=runs.filter(x=>['complete','completed','success','succeeded','ok'].includes(String(x.status||'').toLowerCase())).length;
 return <>
  <div className="eyebrow">Source operations</div><h1 className="title">Data health</h1><p className="subtitle">Identify freshness, completeness, continuity and source issues before they affect recommendations.</p>
  <div className="healthsummary">
   <article><span className={providerAvailable?'status-ok':'status-review'}>{providerAvailable?'● Demo snapshot available':'○ Source unavailable'}</span><b>Overall status</b><p>{providerAvailable?'MockProvider evidence is available for product evaluation.':'Recommendations should not be treated as current.'}</p></article>
   <article><strong>Not calculated</strong><b>Metric completeness</b><p>A real percentage requires the licensed provider field contract.</p></article>
   <article><strong>{successfulRuns} logged</strong><b>Successful collection runs</b><p>Based only on recorded provider-run statuses.</p></article>
   <article><strong>Not assessed</strong><b>Cross-source discrepancies</b><p>No second authorized source is connected for reconciliation.</p></article>
  </div>
  <section className="panel"><h2>Provider status</h2><div className="healthrow"><span><i/> {o.provider||'Unavailable'}</span><b>{o.data_mode==='Demo'?'Demo only':providerAvailable?'Evidence available':'Unavailable'}</b><small>Provider freshness: {o.provider_freshness?new Date(o.provider_freshness).toLocaleString('en-GB'):'Unavailable'}</small></div><h2>Collection-run log</h2><table className="table"><thead><tr><th>Started</th><th>Provider</th><th>Status</th><th>Quality</th><th>Decision impact</th></tr></thead><tbody>{runs.slice(0,8).map((x,i)=>{const ok=['complete','completed','success','succeeded','ok'].includes(String(x.status||'').toLowerCase());return <tr key={i}><td>{x.started_at?new Date(x.started_at).toLocaleString('en-GB'):'Unavailable'}</td><td>{x.provider}</td><td><span className={ok?'status-ok':'status-review'}>{ok?'✓':'!'} {x.status||'Unknown'}</span></td><td>{x.quality?JSON.stringify(x.quality):'Not reported'}</td><td>{ok?'Demo evidence retained':'Review freshness before acting'}</td></tr>})}</tbody></table>{!runs.length&&<div className="notice"><b>No collection-run evidence.</b> Run the collector or connect an authorized provider before treating freshness as known.</div>}</section>
 </>
}
