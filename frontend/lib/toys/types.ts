export type DataMode = 'demo' | 'live' | 'unavailable';
export type TrendLifecycle =
  | 'Insufficient evidence'
  | 'Emerging'
  | 'Accelerating'
  | 'Breakout'
  | 'Viral'
  | 'Saturated'
  | 'Declining'
  | 'Recurring';
export type DecisionRecommendation = 'Act' | 'Monitor' | 'Avoid';
export type Confidence = 'High' | 'Medium' | 'Low';
export type FreshnessStatus = 'Fresh' | 'Stale' | 'Unavailable';
export type SafetyState = 'Clear' | 'Review' | 'Hold';

export interface DataProvenance {
  mode: DataMode;
  mode_label: string;
  coverage: string;
  provider?: string;
  last_observation?: string | null;
}

export interface ToyVideoEvidence {
  id: string;
  caption: string;
  creator: string;
  creator_type?: string;
  published_at: string | null;
  canonical_url: string;
  views: number | null;
  growth: number | null;
  velocity: number | null;
  hashtags: string[];
  sound: string | null;
  market: string;
  evidence_type: string;
  missing_fields: string[];
}

export interface SignalRelationships {
  hashtags: string[];
  sounds: string[];
  creator_types: string[];
  market_notes: string[];
}

export interface SignalQuality {
  snapshot_count: number;
  first_observed: string | null;
  last_observed: string | null;
  missing_fields: string[];
  coverage_limitations: string[];
  provider: string;
  cohort_size: number;
  confidence_explanation: string;
}

export interface SignalRisks {
  safety: string[];
  copyright: string[];
  product_claims: string[];
  music_rights: string;
  child_privacy: string[];
  evidence_limitations: string[];
}

export interface ToySignal {
  id: string;
  title: string;
  conclusion: string;
  category: string;
  mechanism: string;
  lifecycle: TrendLifecycle;
  recommendation: DecisionRecommendation;
  markets: string[];
  languages: string[];
  opportunity_score: number | null;
  confidence: Confidence;
  confidence_score: number | null;
  freshness_at: string | null;
  freshness_status: FreshnessStatus;
  saturation: number | null;
  velocity: number | null;
  acceleration: number | null;
  creator_spread: number;
  post_count: number;
  snapshot_count: number;
  why_it_matters: string;
  main_limitation: string;
  decision_window: string;
  safety_state: SafetyState;
  score_version: string;
  demo: boolean;
  evidence?: ToyVideoEvidence[];
  relationships?: SignalRelationships;
  quality?: SignalQuality;
  risks?: SignalRisks;
  decision?: {recommendation: DecisionRecommendation; reason?: string; review_date?: string | null} | null;
  opportunity?: CreativeOpportunity | null;
}

export interface ToyCreator {
  id: string;
  username: string;
  display_name: string;
  creator_type: string;
  toy_categories: string[];
  followers: number | null;
  recent_post_count: number;
  baseline_velocity: number | null;
  breakout_signal: string | null;
  market: string;
  evidence_quality: Confidence;
  freshness_at: string | null;
}

export interface ToyHashtag {
  id: string;
  name: string;
  observed_posts: number;
  unique_creators: number;
  creator_growth: number | null;
  related_hashtags: string[];
  categories: string[];
  mechanisms: string[];
  lifecycle: TrendLifecycle;
  saturation: number | null;
  market: string;
  freshness_at: string | null;
}

export interface ToySound {
  id: string;
  title: string;
  toy_post_adoption: number;
  independent_creators: number;
  categories: string[];
  post_momentum: number | null;
  lifecycle: TrendLifecycle;
  freshness_at: string | null;
  rights_status: 'Unknown';
}

export interface ToyWatchlist {
  id: string;
  name: string;
  objective: string;
  categories: string[];
  markets: string[];
  languages: string[];
  last_important_change: string;
  signals_requiring_attention: number;
  last_reviewed: string | null;
  data_status: FreshnessStatus;
}

export interface CreativeOpportunity {
  id: string;
  signal_id: string;
  signal_title: string;
  recommendation: DecisionRecommendation;
  title: string;
  toy_category: string;
  content_mechanism: string;
  why_it_is_moving: string;
  audience_need: string;
  original_hook: string;
  content_structure: string[];
  creator_type: string;
  production_complexity: string;
  decision_window: string;
  elements_not_to_copy: string[];
  safety_considerations: string[];
  rights_considerations: string[];
  evidence_limitations: string[];
  review_status: string;
  include_in_report: boolean;
}

export interface ToyReport {
  id: string | number;
  date: string;
  status: string;
  executive_summary: string;
  act: ToySignal[];
  monitor: ToySignal[];
  avoid: ToySignal[];
  opportunities: CreativeOpportunity[];
  limitations: string[];
  methodology: string;
}

export interface ProviderHealth {
  name: string;
  state: string;
  last_success: string | null;
  last_observation: string | null;
  freshness_status: FreshnessStatus;
  quality_status: string;
}

export interface ToyOverview {
  mode: DataMode;
  mode_label: string;
  coverage: string;
  provider: ProviderHealth;
  since_last_review: Array<{type: string; label: string; count: number; detail: string}>;
  decision_queue: Record<'act' | 'monitor' | 'avoid', ToySignal[]>;
  market_pulse: {
    categories: string[];
    hashtags: string[];
    creators: string[];
    mechanisms: string[];
    sounds: string[];
  };
  report_readiness: {
    opportunities_selected: number;
    notes_completed: number;
    awaiting_review: number;
    status: string;
  };
}

export interface EntityCollection<T> extends DataProvenance {
  items: T[];
  total: number;
}
