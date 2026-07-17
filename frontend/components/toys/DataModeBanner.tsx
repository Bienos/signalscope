import type {DataMode, FreshnessStatus} from '../../lib/toys/types';
import {displayDateTime} from '../../lib/toys/formatters';

export function DataModeBanner({
  mode,
  modeLabel,
  coverage,
  provider,
  lastObservation,
  freshness = 'Unavailable',
}: {
  mode: DataMode;
  modeLabel: string;
  coverage: string;
  provider?: string;
  lastObservation?: string | null;
  freshness?: FreshnessStatus;
}) {
  const label = mode === 'demo' ? 'DEMO TOY DATA' : modeLabel || 'DATA UNAVAILABLE';
  return (
    <aside className={`modebanner mode-${mode}`} aria-label="Data source and coverage">
      <strong>{label}</strong>
      <span>{provider || 'Provider unavailable'}</span>
      <span>{freshness} · {displayDateTime(lastObservation)}</span>
      <small>{coverage}</small>
    </aside>
  );
}
