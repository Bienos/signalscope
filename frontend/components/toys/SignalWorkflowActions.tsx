'use client';

import Link from 'next/link';
import {useState} from 'react';
import type {DecisionRecommendation} from '../../lib/toys/types';
import {DecisionActions} from './DecisionActions';

export function SignalWorkflowActions({signalId, current}: {signalId: string; current?: DecisionRecommendation}) {
  const [note, setNote] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function post(action: 'notes' | 'save', body: Record<string, unknown>) {
    setBusy(true);
    setMessage('');
    const response = await fetch(`/api/toys/signals/${encodeURIComponent(signalId)}/${action}`, {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body),
    });
    setMessage(response.ok ? 'Saved to the source-linked workflow.' : 'Could not persist this action. No demo-only success has been shown.');
    if (response.ok && action === 'notes') setNote('');
    setBusy(false);
  }

  return <section className="signalworkflow" aria-labelledby="workflow-actions">
    <h2 id="workflow-actions">Decision and next action</h2>
    <DecisionActions signalId={signalId} current={current}/>
    <div className="noteworkflow"><label htmlFor="analyst-note">Analyst note</label><textarea id="analyst-note" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Record why this matters to the client and what evidence is still missing."/><button type="button" disabled={!note.trim() || busy} onClick={() => post('notes', {analyst_note: note})}>Save note</button></div>
    <div className="workflowbuttons">
      <button type="button" disabled={busy} onClick={() => post('save', {include_in_report: false})}>Save opportunity</button>
      <Link className="action secondary" href={`/opportunities?signal=${encodeURIComponent(signalId)}`}>Create creative brief</Link>
      <button type="button" disabled={busy} onClick={() => post('save', {include_in_report: true})}>Add to report</button>
    </div>
    {message && <p role="status">{message}</p>}
  </section>;
}
