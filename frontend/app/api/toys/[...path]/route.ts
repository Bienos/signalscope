import {NextRequest, NextResponse} from 'next/server';
import {apiBase, requestAuthorization} from '../../../../lib/server-session';
const allowedPostPaths = [
  /^signals\/[^/]+\/(decision|notes|save|create-brief)$/,
  /^reports$/,
  /^opportunities\/[^/]+$/,
];

export async function POST(
  request: NextRequest,
  context: {params: Promise<{path: string[]}>},
) {
  const {path} = await context.params;
  const joined = path.join('/');
  if (!allowedPostPaths.some((rule) => rule.test(joined))) {
    return NextResponse.json({detail: 'Unsupported toy workflow action'}, {status: 404});
  }

  try {
    const authorization = requestAuthorization(request);
    if (!authorization) {
      return NextResponse.json(
        {detail: 'Sign in before changing the persistent toy workflow.'},
        {status: 401},
      );
    }
    const body = await request.text();
    const response = await fetch(`${apiBase}/api/toys/${joined}`, {
      method: 'POST',
      headers: {
        Authorization: authorization,
        'Content-Type': 'application/json',
      },
      body,
      cache: 'no-store',
    });
    const text = await response.text();
    return new NextResponse(text || null, {
      status: response.status,
      headers: {'Content-Type': response.headers.get('content-type') || 'application/json'},
    });
  } catch {
    return NextResponse.json(
      {detail: 'The toy decision service is unavailable; demo content was not changed.'},
      {status: 503},
    );
  }
}
