import Link from 'next/link';
import {displayCompactMetric, displayMetric} from '../../lib/toys/formatters';
import type {ToySignal} from '../../lib/toys/types';
import {ConfidencePill, StatusPill} from './StatusPill';

export function SignalCard({signal, compact = false}: {signal: ToySignal; compact?: boolean}) {
  return (
    <article className={`toysignalcard recommendation-${signal.recommendation.toLowerCase()}`}>
      <header>
        <div className="pillrow">
          <StatusPill value={signal.recommendation} />
          <span className="lifecyclepill">{signal.lifecycle}</span>
        </div>
        <span className="toyscore">
          {signal.opportunity_score === null ? 'Score unavailable' : `TOS ${signal.opportunity_score}`}
        </span>
      </header>
      <h2>{signal.title}</h2>
      <p className="signalconclusion">{signal.conclusion}</p>
      <div className="signalcontext">
        <span>{signal.category}</span>
        <span>{signal.mechanism}</span>
        <span>{signal.markets.join(' · ')}</span>
      </div>
      {!compact && <p className="whymatters"><b>Why it matters</b>{signal.why_it_matters}</p>}
      <dl className="signalmetrics">
        <div><dt>Velocity</dt><dd>{displayCompactMetric(signal.velocity)}{signal.velocity !== null ? '/hr' : ''}</dd></div>
        <div><dt>Acceleration</dt><dd>{displayMetric(signal.acceleration, signal.acceleration !== null ? '×' : '')}</dd></div>
        <div><dt>Creators</dt><dd>{signal.creator_spread}</dd></div>
        <div><dt>Saturation</dt><dd>{displayMetric(signal.saturation, signal.saturation !== null ? '%' : '')}</dd></div>
      </dl>
      <div className="signaltrust">
        <ConfidencePill value={signal.confidence} />
        <StatusPill value={signal.freshness_status} />
        <StatusPill value={signal.safety_state} label={`Safety: ${signal.safety_state}`} />
      </div>
      {!compact && <p className="limitation"><b>Main limitation:</b> {signal.main_limitation}</p>}
      {!compact && signal.recommendation === 'Monitor' && <p className="limitation"><b>What would move it to Act:</b> A fresh observation confirming acceleration, broader independent-creator adoption and no unresolved safety or rights hold.</p>}
      <footer>
        <span>{signal.decision_window}</span>
        <Link className="action secondary" href={`/signals/${signal.id}`}>Inspect evidence</Link>
      </footer>
    </article>
  );
}
