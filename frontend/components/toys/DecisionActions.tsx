'use client';

import {useState} from 'react';
import type {DecisionRecommendation} from '../../lib/toys/types';

export function DecisionActions({signalId, current}: {signalId: string; current?: DecisionRecommendation}) {
  const [decision, setDecision] = useState<DecisionRecommendation | undefined>(current);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function choose(next: DecisionRecommendation) {
    setBusy(true);
    setMessage('');
    const response = await fetch(`/api/toys/signals/${encodeURIComponent(signalId)}/decision`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({decision: next, recommendation: next}),
    });
    if (response.ok) {
      setDecision(next);
      setMessage(`Saved as ${next}.`);
    } else {
      setMessage('Could not persist this decision. The displayed demo evidence is unchanged.');
    }
    setBusy(false);
  }

  return (
    <div className="decisionactions" aria-label="Signal decision">
      {(['Act', 'Monitor', 'Avoid'] as const).map((value) => (
        <button
          key={value}
          type="button"
          aria-pressed={decision === value}
          disabled={busy}
          onClick={() => choose(value)}
        >{value}</button>
      ))}
      {message && <span role="status">{message}</span>}
    </div>
  );
}
