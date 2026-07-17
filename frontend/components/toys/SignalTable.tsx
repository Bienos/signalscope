import Link from 'next/link';
import {displayCompactMetric, displayDateTime, displayMetric} from '../../lib/toys/formatters';
import type {ToySignal} from '../../lib/toys/types';
import {ConfidencePill, StatusPill} from './StatusPill';

export function SignalTable({signals}: {signals: ToySignal[]}) {
  if (!signals.length) return <div className="empty"><b>No toy signals match these filters.</b><p>Broaden the filters or review another lifecycle.</p></div>;
  return (
    <div className="tablewrap toytablewrap">
      <table className="table toysignaltable">
        <caption>Toy-market signals with decision, evidence quality and freshness</caption>
        <thead><tr>
          <th>Signal</th><th>Decision</th><th>Lifecycle</th><th>Velocity</th><th>Acceleration</th>
          <th>Creators</th><th>Confidence</th><th>Safety</th><th>Freshness</th><th><span className="sr-only">Action</span></th>
        </tr></thead>
        <tbody>{signals.map((signal) => <tr key={signal.id}>
          <td data-label="Signal"><b>{signal.title}</b><small>{signal.category} · {signal.mechanism}</small></td>
          <td data-label="Decision"><StatusPill value={signal.recommendation} /></td>
          <td data-label="Lifecycle">{signal.lifecycle}</td>
          <td data-label="Velocity" className="numeric">{displayCompactMetric(signal.velocity)}{signal.velocity !== null ? '/hr' : ''}</td>
          <td data-label="Acceleration" className="numeric">{displayMetric(signal.acceleration, signal.acceleration !== null ? '×' : '')}</td>
          <td data-label="Creators" className="numeric">{signal.creator_spread}</td>
          <td data-label="Confidence"><ConfidencePill value={signal.confidence} /></td>
          <td data-label="Safety"><StatusPill value={signal.safety_state} /></td>
          <td data-label="Freshness"><StatusPill value={signal.freshness_status} /><small>{displayDateTime(signal.freshness_at)}</small></td>
          <td data-label="Action"><Link className="tableaction" href={`/signals/${signal.id}`} aria-label={`Inspect ${signal.title}`}>Inspect →</Link></td>
        </tr>)}</tbody>
      </table>
    </div>
  );
}
