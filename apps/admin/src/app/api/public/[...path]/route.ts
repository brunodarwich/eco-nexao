function apiBaseUrl() {
  return (
    process.env.ECONEXAO_API_INTERNAL_URL ?? 'http://localhost:8000/api/v1'
  ).replace(/\/$/, '')
}

interface RouteContext {
  params: Promise<{ path: string[] }>
}

export async function GET(request: Request, context: RouteContext) {
  const { path: segments } = await context.params
  const path = segments.join('/')
  const requestUrl = new URL(request.url)
  const target = new URL(`${apiBaseUrl()}/${path}`)
  target.search = requestUrl.search

  try {
    const upstream = await fetch(target, {
      cache: 'no-store',
      headers: { Accept: 'application/json' },
      method: 'GET',
    })
    return new Response(await upstream.arrayBuffer(), {
      headers: {
        'Cache-Control': 'no-store',
        'Content-Type':
          upstream.headers.get('content-type') ?? 'application/json',
      },
      status: upstream.status,
    })
  } catch {
    return Response.json(
      {
        code: 'public_api_unavailable',
        message: 'A API pública está indisponível.',
      },
      {
        headers: { 'Cache-Control': 'no-store' },
        status: 502,
      },
    )
  }
}
