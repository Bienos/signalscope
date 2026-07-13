import {confidenceIcon, statusTone} from '../../lib/toys/formatters';
import type {
  Confidence,
  DecisionRecommendation,
  FreshnessStatus,
  SafetyState,
} from '../../lib/toys/types';

export function StatusPill({
  value,
  label,
}: {
  value: DecisionRecommendation | FreshnessStatus | SafetyState;
  label?: string;
}) {
  return <span className={`statuspill tone-${statusTone(value)}`}>{label || value}</span>;
}

export function ConfidencePill({value}: {value: Confidence}) {
  return <span className="confidencepill"><span aria-hidden="true">{confidenceIcon(value)}</span> {value} confidence</span>;
}
