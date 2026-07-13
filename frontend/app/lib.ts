import {cookies} from 'next/headers';
import {apiBase, explicitDemoMode, sessionCookieName} from '../lib/server-session';

export async function api<T>(path: string, fallback: T): Promise<T> {
  const token = (await cookies()).get(sessionCookieName)?.value;
  if (!token && explicitDemoMode()) return fallback;
  if (!token) throw new Error('Authentication is required to load live SignalScope data.');
  try {
    const response = await fetch(`${apiBase}${path}`, {
      headers: {Authorization: `Bearer ${token}`},
      cache: 'no-store',
    });
    if (response.ok) return await response.json() as T;
    if (explicitDemoMode()) return fallback;
    throw new Error(`SignalScope API returned ${response.status}.`);
  } catch (error) {
    if (explicitDemoMode()) return fallback;
    throw error;
  }
}
