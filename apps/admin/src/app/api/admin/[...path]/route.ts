const allowedPaths = new Set([
  'auth/csrf',
  'auth/login',
  'auth/session',
  'auth/logout',
  'discovery/google-places/preview',
  'editorial/revisions',
  'audit-logs',
  'imports/validate',
  'imports/commit',
  'reports',
  'analytics/summary',
])

interface RouteContext {
  params: Promise<{ path: string[] }>
}

function apiBaseUrl() {
  return (
    process.env.ECONEXAO_API_INTERNAL_URL ?? 'http://localhost:8000/api/v1'
  ).replace(/\/$/, '')
}

async function proxyRequest(request: Request, context: RouteContext) {
  const { path: segments } = await context.params
  const path = segments.join('/')

  // Suporte a caminhos dinâmicos como 'reports/<id>'
  const isAllowed =
    allowedPaths.has(path) ||
    allowedPaths.has(segments[0]) ||
    (segments.length >= 2 && allowedPaths.has(`${segments[0]}/${segments[1]}`))

  if (!isAllowed) {
    return Response.json(
      { message: 'Recurso não encontrado.' },
      { status: 404 },
    )
  }

  const requestUrl = new URL(request.url)
  const target = new URL(`${apiBaseUrl()}/admin/${path}`)
  target.search = requestUrl.search
  const headers = new Headers({ Accept: 'application/json' })
  for (const name of ['content-type', 'cookie', 'origin', 'x-csrftoken']) {
    const value = request.headers.get(name)
    if (value) headers.set(name, value)
  }

  try {
    const upstream = await fetch(target, {
      body:
        request.method === 'GET' || request.method === 'HEAD'
          ? undefined
          : await request.arrayBuffer(),
      cache: 'no-store',
      headers,
      method: request.method,
      redirect: 'manual',
    })
    const responseHeaders = new Headers({
      'Cache-Control': 'no-store',
      'Content-Type':
        upstream.headers.get('content-type') ?? 'application/json',
    })
    for (const name of ['set-cookie', 'x-request-id']) {
      const value = upstream.headers.get(name)
      if (value) responseHeaders.set(name, value)
    }
    return new Response(await upstream.arrayBuffer(), {
      headers: responseHeaders,
      status: upstream.status,
    })
  } catch {
    return Response.json(
      {
        code: 'admin_api_unavailable',
        message: 'A API administrativa está indisponível.',
      },
      {
        headers: { 'Cache-Control': 'no-store' },
        status: 502,
      },
    )
  }
}

export function GET(request: Request, context: RouteContext) {
  return proxyRequest(request, context)
}

export function POST(request: Request, context: RouteContext) {
  return proxyRequest(request, context)
}

export function PATCH(request: Request, context: RouteContext) {
  return proxyRequest(request, context)
}

export function PUT(request: Request, context: RouteContext) {
  return proxyRequest(request, context)
}

export function DELETE(request: Request, context: RouteContext) {
  return proxyRequest(request, context)
}
