import {api} from '../../app/lib';
import {explicitDemoMode} from '../server-session';
import {
  demoCollection,
  demoCreators,
  demoHashtags,
  demoOpportunities,
  demoOverview,
  demoReports,
  demoSignals,
  demoSounds,
  demoWatchlists,
} from './fixtures';
import type {
  CreativeOpportunity,
  EntityCollection,
  ToyCreator,
  ToyHashtag,
  ToyOverview,
  ToyReport,
  ToySignal,
  ToySound,
  ToyWatchlist,
} from './types';

type CollectionResponse<T> = EntityCollection<T> | T[];

const asCollection = <T>(
  value: CollectionResponse<T> | null | undefined,
  fallback: T[],
): EntityCollection<T> => {
  if (Array.isArray(value)) return demoCollection(value);
  if (value && Array.isArray(value.items)) return value;
  if (explicitDemoMode()) return demoCollection(fallback);
  throw new Error('The live SignalScope API returned an invalid collection contract.');
};

export async function getToyOverview(): Promise<ToyOverview> {
  return api<ToyOverview>('/api/toys/overview', demoOverview);
}

export async function getToySignals(query = ''): Promise<EntityCollection<ToySignal>> {
  const fallback = demoCollection(demoSignals);
  const response = await api<CollectionResponse<ToySignal>>(`/api/toys/signals${query}`, fallback);
  return asCollection(response, demoSignals);
}

export async function getToySignal(id: string): Promise<ToySignal | null> {
  const fallback = demoSignals.find((signal) => signal.id === id) ?? null;
  return api<ToySignal | null>(`/api/toys/signals/${encodeURIComponent(id)}`, fallback);
}

export async function getToyCreators(): Promise<EntityCollection<ToyCreator>> {
  const fallback = demoCollection(demoCreators);
  return asCollection(await api<CollectionResponse<ToyCreator>>('/api/toys/creators', fallback), demoCreators);
}

export async function getToyHashtags(): Promise<EntityCollection<ToyHashtag>> {
  const fallback = demoCollection(demoHashtags);
  return asCollection(await api<CollectionResponse<ToyHashtag>>('/api/toys/hashtags', fallback), demoHashtags);
}

export async function getToySounds(): Promise<EntityCollection<ToySound>> {
  const fallback = demoCollection(demoSounds);
  return asCollection(await api<CollectionResponse<ToySound>>('/api/toys/sounds', fallback), demoSounds);
}

export async function getToyWatchlists(): Promise<EntityCollection<ToyWatchlist>> {
  const fallback = demoCollection(demoWatchlists);
  return asCollection(await api<CollectionResponse<ToyWatchlist>>('/api/toys/watchlists', fallback), demoWatchlists);
}

export async function getToyOpportunities(): Promise<EntityCollection<CreativeOpportunity>> {
  const fallback = demoCollection(demoOpportunities);
  return asCollection(
    await api<CollectionResponse<CreativeOpportunity>>('/api/toys/opportunities', fallback),
    demoOpportunities,
  );
}

export async function getToyReports(): Promise<EntityCollection<ToyReport>> {
  const fallback = demoCollection(demoReports);
  return asCollection(await api<CollectionResponse<ToyReport>>('/api/toys/reports', fallback), demoReports);
}
