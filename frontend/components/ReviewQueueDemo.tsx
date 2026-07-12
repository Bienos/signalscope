'use client';
import {useState} from 'react';

type ReviewItem={id:number;caption:string;creator:string;market:string;category:string};
const actions=['Approved for analysis','Allowed with warning','Excluded from recommendations','Escalated'];

export function ReviewQueueDemo({rows}:{rows:ReviewItem[]}){
 const [decisions,setDecisions]=useState<Record<number,string>>({});
 return <><div className="eyebrow">Team workflow · local demo</div><h1 className="title">Review queue <span className="countbadge">{rows.filter(x=>!decisions[x.id]).length}</span></h1><p className="subtitle">Resolve safety, intellectual-property, missing-evidence and classification questions. Decisions below work locally for this session; shared persistence and audit history are planned.</p><div className="queue">{rows.map((x,i)=><article className="reviewcard" key={x.id}><header><span className={decisions[x.id]?'status-ok':'status-review'}>{decisions[x.id]?`✓ ${decisions[x.id]}`:'! Review required'}</span><small>Demo case {i+1}</small></header><h2>{x.caption}</h2><p>@{x.creator} · {x.market} · {x.category}</p><div className="reviewreason"><b>{i?'Brand/IP visibility':'Safety classification'}</b><span>{i?'Distinctive protected elements may limit adaptation.':'Do not recommend until a human confirms the handling outcome.'}</span></div><footer>{actions.map(action=><button key={action} aria-pressed={decisions[x.id]===action} onClick={()=>setDecisions(current=>({...current,[x.id]:action}))}>{action}</button>)}</footer></article>)}</div><div className="notice"><b>Commercial boundary.</b> This demonstrates the Team decision workflow. User identity, database persistence, permissions and a durable audit log are not implemented.</div></>
}
