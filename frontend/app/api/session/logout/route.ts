import {NextResponse} from 'next/server';
import {sessionCookieName} from '../../../../lib/server-session';

export async function POST() {
  const response = NextResponse.json({authenticated: false});
  response.cookies.set(sessionCookieName, '', {
    httpOnly: true,
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production'
      && process.env.SIGNALSCOPE_SESSION_COOKIE_SECURE !== 'false',
    path: '/',
    maxAge: 0,
  });
  return response;
}
