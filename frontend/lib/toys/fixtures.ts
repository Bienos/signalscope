import demo from './demo-fixtures.json';
import type {
  CreativeOpportunity,
  EntityCollection,
  ToyCreator,
  ToyHashtag,
  ToyOverview,
  ToyReport,
  ToySignal,
  ToySound,
  ToyVideoEvidence,
  ToyWatchlist,
} from './types';

type EvidenceSeed = ToyVideoEvidence & {signal_id: string};
const evidence = demo.videos as unknown as EvidenceSeed[];
export const demoSignals = (demo.signals as unknown as ToySignal[]).map((signal) => ({
  ...signal,
  evidence: [
    ...(signal.evidence || []),
    ...evidence.filter((item) => item.signal_id === signal.id).map((seed) => {
      const item = {...seed} as Partial<EvidenceSeed>;
      delete item.signal_id;
      return item as ToyVideoEvidence;
    }),
  ],
}));
export const demoCreators = demo.creators as unknown as ToyCreator[];
export const demoHashtags = demo.hashtags as unknown as ToyHashtag[];
export const demoSounds = demo.sounds as unknown as ToySound[];
export const demoWatchlists = demo.watchlists as unknown as ToyWatchlist[];
export const demoOpportunities = demo.opportunities as unknown as CreativeOpportunity[];

export const demoReports: ToyReport[] = demo.reports.map((reportSeed) => ({
    ...reportSeed,
    act: demoSignals.filter((signal) => signal.recommendation === 'Act'),
    monitor: demoSignals.filter((signal) => signal.recommendation === 'Monitor'),
    avoid: demoSignals.filter((signal) => signal.recommendation === 'Avoid'),
    opportunities: demoOpportunities,
  } as ToyReport));

export const demoOverview: ToyOverview = {
  mode: 'demo',
  mode_label: 'DEMO TOY DATA',
  coverage: 'Synthetic configured sample for product evaluation; not complete TikTok coverage.',
  provider: {
    name: 'MockProvider',
    state: 'Available',
    last_success: '2026-07-13T07:20:00Z',
    last_observation: '2026-07-13T07:20:00Z',
    freshness_status: 'Fresh',
    quality_status: 'Synthetic fixtures validated',
  },
  since_last_review: [
    {type: 'new_signal', label: 'New signals', count: 3, detail: 'Three signals entered the monitored sample.'},
    {type: 'lifecycle', label: 'Lifecycle changes', count: 2, detail: 'Blind-box reveals accelerated; plush collections saturated.'},
    {type: 'creator_spread', label: 'Creator adoption', count: 5, detail: 'Five new independent creator associations.'},
    {type: 'safety', label: 'Safety reviews', count: 2, detail: 'Heating and projectile handling require review.'},
  ],
  decision_queue: {
    act: demoSignals.filter((signal) => signal.recommendation === 'Act'),
    monitor: demoSignals.filter((signal) => signal.recommendation === 'Monitor'),
    avoid: demoSignals.filter((signal) => signal.recommendation === 'Avoid'),
  },
  market_pulse: {
    categories: ['Blind boxes and collectibles', 'Construction toys', 'Screen-free toys'],
    hashtags: ['#blindbox', '#zabawkiedukacyjne', '#screenfreetoys'],
    creators: ['@collectorbench', '@zabawkowytest', '@rodzinnyczas'],
    mechanisms: ['Blind reveal', 'Stress test', 'Parent recommendation'],
    sounds: ['Reveal pulse', 'Original sound — buildbench', 'Soft click loop'],
  },
  report_readiness: {
    opportunities_selected: 1,
    notes_completed: 1,
    awaiting_review: 2,
    status: 'Draft requires review',
  },
};

export const demoCollection = <T>(items: T[]): EntityCollection<T> => ({
  items,
  total: items.length,
  mode: 'demo',
  mode_label: 'DEMO TOY DATA',
  coverage: 'Synthetic configured sample for product evaluation; not complete TikTok coverage.',
  provider: 'MockProvider',
  last_observation: '2026-07-13T07:20:00Z',
});
