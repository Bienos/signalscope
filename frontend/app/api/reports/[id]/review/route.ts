import {NextRequest, NextResponse} from 'next/server';
import {apiBase, requestAuthorization} from '../../../../../lib/server-session';

export async function POST(
  request: NextRequest,
  {params}: {params: Promise<{id: string}>},
) {
  const authorization = requestAuthorization(request);
  if (!authorization) return NextResponse.json({detail: 'Sign in to review a report'}, {status: 401});
  try {
    const {id} = await params;
    const value = await request.json() as {useful?: boolean; note?: string};
    const query = new URLSearchParams();
    if (value.useful !== undefined) query.set('useful', String(value.useful));
    if (value.note) query.set('note', value.note);
    const response = await fetch(`${apiBase}/api/reports/${id}/review?${query}`, {
      method: 'POST',
      headers: {Authorization: authorization},
      cache: 'no-store',
    });
    return NextResponse.json(await response.json(), {status: response.status});
  } catch {
    return NextResponse.json({detail: 'Review service unavailable'}, {status: 503});
  }
}

