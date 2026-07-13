import {NextRequest, NextResponse} from 'next/server';
import {apiBase, sessionCookieName} from '../../../../lib/server-session';

export async function POST(request: NextRequest) {
  try {
    const credentials = await request.json() as {username?: string; password?: string};
    if (!credentials.username || !credentials.password) {
      return NextResponse.json({detail: 'Email and password are required'}, {status: 422});
    }
    const body = new URLSearchParams({
      username: credentials.username,
      password: credentials.password,
    });
    const response = await fetch(`${apiBase}/api/auth/token`, {
      method: 'POST',
      body,
      cache: 'no-store',
    });
    if (!response.ok) {
      return NextResponse.json({detail: 'Incorrect email or password'}, {status: 401});
    }
    const payload = await response.json() as {access_token?: string};
    if (!payload.access_token) {
      return NextResponse.json({detail: 'The authentication service returned no session'}, {status: 502});
    }
    const result = NextResponse.json({authenticated: true});
    result.cookies.set(sessionCookieName, payload.access_token, {
      httpOnly: true,
      sameSite: 'strict',
      secure: process.env.NODE_ENV === 'production'
        && process.env.SIGNALSCOPE_SESSION_COOKIE_SECURE !== 'false',
      path: '/',
      maxAge: 8 * 60 * 60,
    });
    return result;
  } catch {
    return NextResponse.json({detail: 'Authentication service unavailable'}, {status: 503});
  }
}
