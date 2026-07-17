'use client';

import Link from 'next/link';
import {useMemo, useState} from 'react';
import type {CreativeOpportunity, ToySignal} from '../../lib/toys/types';
import {DecisionActions} from './DecisionActions';
import {ConfidencePill, StatusPill} from './StatusPill';

const originalityChecks = [
  'Use new wording and an original hook',
  'Use original footage, setting and narrative result',
  'Do not imitate an identifiable creator',
  'Use original or cleared audio',
];
const safetyChecks = [
  'Review toy-specific safety risks',
  'Avoid unsupported developmental or educational claims',
  'Protect child privacy and avoid identifiable-child imitation',
  'Verify copyright and licensed-character permissions',
];
const allChecks = [...originalityChecks, ...safetyChecks];

export function OpportunityWorkspace({
  signals,
  initialOpportunities,
  initialSignalId,
}: {
  signals: ToySignal[];
  initialOpportunities: CreativeOpportunity[];
  initialSignalId?: string;
}) {
  const [opportunities, setOpportunities] = useState(initialOpportunities);
  const [selectedId, setSelectedId] = useState(
    signals.some((signal) => signal.id === initialSignalId)
      ? initialSignalId as string
      : signals.find((s) => s.recommendation === 'Act')?.id || signals[0]?.id || '',
  );
  const [hook, setHook] = useState('');
  const [audienceNeed, setAudienceNeed] = useState('');
  const [checks, setChecks] = useState<Record<string, boolean>>(
    () => Object.fromEntries(allChecks.map((check) => [check, false])),
  );
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const selected = signals.find((signal) => signal.id === selectedId);
  const ready = allChecks.every((check) => checks[check]) && hook.trim() && audienceNeed.trim();
  const grouped = useMemo(() => ({
    Act: signals.filter((signal) => signal.recommendation === 'Act'),
    Monitor: signals.filter((signal) => signal.recommendation === 'Monitor'),
    Avoid: signals.filter((signal) => signal.recommendation === 'Avoid'),
  }), [signals]);

  async function createBrief() {
    if (!selected || !ready) return;
    setBusy(true);
    setMessage('');
    const response = await fetch(`/api/toys/signals/${encodeURIComponent(selected.id)}/create-brief`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        title: hook.trim(),
        audience_need: audienceNeed.trim(),
        original_hook: hook.trim(),
        originality_checks: Object.fromEntries(originalityChecks.map((item) => [item, checks[item]])),
        safety_checks: Object.fromEntries(safetyChecks.map((item) => [item, checks[item]])),
      }),
    });
    if (response.ok) {
      const value = (await response.json()) as CreativeOpportunity;
      if (value?.id) setOpportunities((current) => [value, ...current.filter((item) => item.id !== value.id)]);
      setMessage('Creative brief persisted and linked to its source signal.');
      setHook('');
      setAudienceNeed('');
      setChecks(Object.fromEntries(allChecks.map((check) => [check, false])));
    } else {
      setMessage('Could not persist the brief. No demo-only success has been shown.');
    }
    setBusy(false);
  }

  return <>
    <nav className="opportunitytabs" aria-label="Opportunity decision groups">
      {(['Act', 'Monitor', 'Avoid'] as const).map((decision) => (
        <a href={`#${decision.toLowerCase()}`} key={decision}>{decision} <b>{grouped[decision].length}</b></a>
      ))}
      <a href="#creative-briefs">Creative briefs <b>{opportunities.length}</b></a>
      <a href="#needs-review">Needs review <b>{opportunities.filter((item) => item.review_status !== 'Approved').length}</b></a>
    </nav>

    {(['Act', 'Monitor', 'Avoid'] as const).map((decision) => (
      <section className="opportunitysection" id={decision.toLowerCase()} key={decision}>
        <div className="sectionhead"><div><span className="eyebrow">Decision queue</span><h2>{decision}</h2></div></div>
        <div className="opportunityqueue">{grouped[decision].map((signal) => (
          <article key={signal.id}>
            <header><StatusPill value={signal.recommendation}/><ConfidencePill value={signal.confidence}/></header>
            <h3>{signal.title}</h3>
            <p>{signal.conclusion}</p>
            <small><b>Decision window:</b> {signal.decision_window}</small>
            <small><b>Limitation:</b> {signal.main_limitation}</small>
            <footer><DecisionActions signalId={signal.id}/><Link href={`/signals/${signal.id}`}>Evidence →</Link></footer>
          </article>
        ))}</div>
      </section>
    ))}

    <section className="briefbuilder" id="creative-briefs">
      <div><span className="eyebrow">Source-linked workflow</span><h2>Create an original toy content brief</h2><p>Confirm originality, safety and rights checks yourself. None begins checked.</p></div>
      <div className="briefgrid">
        <div className="panel">
          <label className="field">Source signal<select value={selectedId} onChange={(event) => setSelectedId(event.target.value)}>{signals.map((signal) => <option value={signal.id} key={signal.id}>{signal.title}</option>)}</select></label>
          {selected && <div className="sourcebox"><b>{selected.category} · {selected.mechanism}</b><p>{selected.why_it_matters}</p><small>{selected.main_limitation}</small></div>}
          <label className="field">Audience need<textarea value={audienceNeed} onChange={(event) => setAudienceNeed(event.target.value)} placeholder="What useful audience need will this answer?"/></label>
          <label className="field">Original hook<textarea value={hook} onChange={(event) => setHook(event.target.value)} placeholder="Write a new hook; do not copy source wording."/></label>
        </div>
        <div className="panel briefchecks">
          <h3>Originality</h3>
          {originalityChecks.map((check) => <label key={check}><input type="checkbox" checked={checks[check]} onChange={() => setChecks((current) => ({...current, [check]: !current[check]}))}/>{check}</label>)}
          <h3>Safety and rights</h3>
          {safetyChecks.map((check) => <label key={check}><input type="checkbox" checked={checks[check]} onChange={() => setChecks((current) => ({...current, [check]: !current[check]}))}/>{check}</label>)}
          <button className="action" type="button" disabled={!ready || busy} onClick={createBrief}>{busy ? 'Saving…' : 'Create and save brief'}</button>
          {message && <p role="status">{message}</p>}
        </div>
      </div>
    </section>

    <section className="opportunitysection" id="needs-review">
      <div className="sectionhead"><div><span className="eyebrow">Persistent opportunities</span><h2>Creative briefs</h2></div></div>
      <div className="briefcards">{opportunities.map((item) => <article className="panel" key={item.id}>
        <header><StatusPill value={item.recommendation}/><span className="lifecyclepill">{item.review_status}</span></header>
        <h3>{item.title}</h3><p>{item.original_hook}</p>
        <dl><div><dt>Source</dt><dd><Link href={`/signals/${item.signal_id}`}>{item.signal_title}</Link></dd></div><div><dt>Category</dt><dd>{item.toy_category}</dd></div><div><dt>Creator type</dt><dd>{item.creator_type}</dd></div><div><dt>Decision window</dt><dd>{item.decision_window}</dd></div></dl>
        <details><summary>Safety, rights and evidence limits</summary><p>{[...item.safety_considerations, ...item.rights_considerations, ...item.evidence_limitations].join(' · ')}</p></details>
      </article>)}</div>
    </section>
  </>;
}
