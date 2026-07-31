import type { components } from '@econexao/contracts/api'

export type RegionSummary = components['schemas']['RegionSummary']
export type RouteDetail = components['schemas']['RouteDetail']
export type RouteCatalogItem = components['schemas']['RouteCatalogItem']
export type RouteSummary = components['schemas']['RouteSummary']

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const publicPath = `/api/public${path}`
  if (
    typeof navigator !== 'undefined' &&
    !navigator.onLine &&
    'caches' in window
  ) {
    const cached = await window.caches.match(publicPath)
    if (cached) return (await cached.json()) as T
  }

  try {
    const timeoutSignal = AbortSignal.timeout(5_000)
    const requestSignal = signal
      ? AbortSignal.any([signal, timeoutSignal])
      : timeoutSignal
    const response = await fetch(publicPath, {
      headers: { Accept: 'application/json' },
      signal: requestSignal,
    })

    if (!response.ok) {
      throw new Error(
        `A API pública respondeu com o status ${response.status}.`,
      )
    }

    return (await response.json()) as T
  } catch (error) {
    if (signal?.aborted) throw error
    if ('caches' in window) {
      const cached = await window.caches.match(publicPath)
      if (cached) return (await cached.json()) as T
    }
    throw error
  }
}

export function getPublishedRegions(signal?: AbortSignal) {
  return getJson<RegionSummary[]>('/regions', signal)
}

export function getPublishedRoutes(regionSlug: string, signal?: AbortSignal) {
  return getJson<RouteSummary[]>(
    `/regions/${encodeURIComponent(regionSlug)}/routes`,
    signal,
  )
}

export function getPublishedRoute(
  regionSlug: string,
  routeSlug: string,
  signal?: AbortSignal,
) {
  return getJson<RouteDetail>(
    `/regions/${encodeURIComponent(regionSlug)}/routes/${encodeURIComponent(routeSlug)}`,
    signal,
  )
}

export function getPublishedRouteCatalog(
  regionSlug: string,
  routeSlug: string,
  signal?: AbortSignal,
) {
  return getJson<RouteCatalogItem[]>(
    `/regions/${encodeURIComponent(regionSlug)}/routes/${encodeURIComponent(routeSlug)}/catalog`,
    signal,
  )
}
