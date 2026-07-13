import type {NextRequest} from 'next/server';

export const apiBase = process.env.API_URL || 'http://api:8000';
export const sessionCookieName = 'signalscope_session';

export function explicitDemoMode() {
  return process.env.SIGNALSCOPE_DEMO_MODE === 'true';
}

export function requestAuthorization(request: NextRequest): string | null {
  const header = request.headers.get('authorization');
  if (header?.startsWith('Bearer ')) return header;
  const token = request.cookies.get(sessionCookieName)?.value;
  return token ? `Bearer ${token}` : null;
}

