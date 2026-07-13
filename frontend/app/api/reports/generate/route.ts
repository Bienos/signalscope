import {NextRequest, NextResponse} from 'next/server';
import {apiBase, requestAuthorization} from '../../../../lib/server-session';

export async function POST(request: NextRequest) {
  const authorization = requestAuthorization(request);
  if (!authorization) return NextResponse.json({detail: 'Sign in to generate a report'}, {status: 401});
  try {
    const response = await fetch(`${apiBase}/api/reports/generate`, {
      method: 'POST',
      headers: {Authorization: authorization},
      cache: 'no-store',
    });
    return NextResponse.json(await response.json(), {status: response.status});
  } catch {
    return NextResponse.json({detail: 'Report service unavailable'}, {status: 503});
  }
}

