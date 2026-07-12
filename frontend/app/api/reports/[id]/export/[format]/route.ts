import {NextRequest, NextResponse} from 'next/server';

const apiBase = process.env.API_URL || 'http://api:8000';

async function demoToken(): Promise<string> {
  const body = new URLSearchParams({
    username: 'admin@viralradar.local',
    password: 'RadarDemo!2026',
  });
  const response = await fetch(`${apiBase}/api/auth/token`, {
    method: 'POST',
    body,
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error('Could not authenticate the report download');
  }
  const payload = (await response.json()) as {access_token: string};
  return payload.access_token;
}

export async function GET(
  _request: NextRequest,
  context: {params: Promise<{id: string; format: string}>},
) {
  try {
    const {id, format} = await context.params;
    if (!/^\d+$/.test(id) || !['csv', 'html', 'xlsx'].includes(format)) {
      return NextResponse.json({detail: 'Invalid report export'}, {status: 400});
    }

    const token = await demoToken();
    const response = await fetch(
      `${apiBase}/api/reports/${id}/export.${format}`,
      {
        headers: {Authorization: `Bearer ${token}`},
        cache: 'no-store',
      },
    );
    if (!response.ok) {
      return NextResponse.json(
        {detail: 'The report could not be exported'},
        {status: response.status},
      );
    }

    const contentType =
      response.headers.get('content-type') ||
      (format === 'xlsx'
        ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        : format === 'csv' ? 'text/csv' : 'text/html');
    const disposition =
      response.headers.get('content-disposition') ||
      `attachment; filename="signalscope-report-${id}.${format}"`;

    return new NextResponse(response.body, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': disposition,
        'Cache-Control': 'no-store',
      },
    });
  } catch {
    return NextResponse.json(
      {detail: 'The report download service is unavailable'},
      {status: 503},
    );
  }
}
