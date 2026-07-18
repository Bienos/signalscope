import type {Confidence, DecisionRecommendation, FreshnessStatus, SafetyState} from './types';

export const displayMetric = (value: number | null | undefined, suffix = ''): string =>
  value === null || value === undefined ? 'Unavailable' : `${value.toLocaleString('en-GB')}${suffix}`;

export const displayCompactMetric = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return 'Unavailable';
  return new Intl.NumberFormat('en-GB', {notation: 'compact', maximumFractionDigits: 1}).format(value);
};

export const displayDateTime = (value: string | null | undefined): string => {
  if (!value) return 'Unavailable';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return 'Unavailable';
  return parsed.toLocaleString('en-GB', {dateStyle: 'medium', timeStyle: 'short'});
};

export const confidenceIcon = (value: Confidence): string =>
  value === 'High' ? '●' : value === 'Medium' ? '◐' : '○';

export const statusTone = (
  value: DecisionRecommendation | FreshnessStatus | SafetyState,
): 'positive' | 'warning' | 'critical' | 'neutral' => {
  if (value === 'Act' || value === 'Fresh' || value === 'Clear') return 'positive';
  if (value === 'Avoid' || value === 'Hold') return 'critical';
  if (value === 'Monitor' || value === 'Stale' || value === 'Review') return 'warning';
  return 'neutral';
};

export const normalizeMode = (mode: unknown): 'demo' | 'live' | 'unavailable' => {
  const value = String(mode || '').toLowerCase();
  if (value.includes('demo') || value.includes('mock')) return 'demo';
  if (value.includes('live') || value.includes('provider')) return 'live';
  return 'unavailable';
};
