'use client';

import {useRouter} from 'next/navigation';
import {useState} from 'react';

export function GenerateToyReport() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const router = useRouter();
  async function generate() {
    setBusy(true); setMessage('');
    const response = await fetch('/api/toys/reports', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({})});
    setMessage(response.ok ? 'Decision report generated from items added to the report.' : response.status === 401 ? 'Sign in before generating a persistent report.' : 'Report service unavailable. The demo report remains unchanged.');
    if (response.ok) router.refresh();
    setBusy(false);
  }
  return <div className="reportgenerate"><button className="action" disabled={busy} onClick={generate}>{busy ? 'Generating…' : 'Generate from selected items'}</button>{message && <span role="status">{message}</span>}</div>;
}
