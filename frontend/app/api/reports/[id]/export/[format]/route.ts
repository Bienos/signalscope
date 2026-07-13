import {NextRequest, NextResponse} from 'next/server';
import {apiBase, requestAuthorization} from '../../../../../../lib/server-session';

export async function GET(
  request: NextRequest,
  context: {params: Promise<{id: string; format: string}>},
) {
  try {
    const {id, format} = await context.params;
    if (!/^\d+$/.test(id) || !['csv', 'html', 'xlsx'].includes(format)) {
      return NextResponse.json({detail: 'Invalid report export'}, {status: 400});
    }

    const authorization = requestAuthorization(request);
    if (!authorization) {
      return NextResponse.json({detail: 'Sign in to export this report'}, {status: 401});
    }
    const response = await fetch(
      `${apiBase}/api/reports/${id}/export.${format}`,
      {
        headers: {Authorization: authorization},
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
