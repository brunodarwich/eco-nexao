export interface PublishedRouteApiSummary {
  id?: string
  slug: string
  public_name: string
  duration_minutes: number
}

export interface RouteReadinessSnapshot {
  actorsCount: number
  catalogScore: number
  contentScore: number
  distanceKm: number
  editorialStatus: 'Rascunho' | 'Em Revisão' | 'Publicado'
  gpxScore: number
  overallScore: number
  stagesCount: number
}

export interface RouteApiSummary {
  id?: string
  durationMinutes: number
  readiness?: RouteReadinessSnapshot
  slug: string
  title: string
}

export function toDashboardRoute(
  route: PublishedRouteApiSummary,
): RouteApiSummary {
  return {
    id: route.id,
    durationMinutes: route.duration_minutes,
    slug: route.slug,
    title: route.public_name,
  }
}
