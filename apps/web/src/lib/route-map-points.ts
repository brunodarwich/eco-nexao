import type { RouteCatalogItem } from './public-api'
import { directionsHref, formatPublicAddress } from './contact-links'

export interface RouteMapPoint {
  actorId: string
  actorSlug: string
  address: string
  categoryName: string
  categorySlug: string
  coordinates: [number, number]
  directionsUrl: string | null
  name: string
  summary: string
}

function validCoordinates(value: number[]): value is [number, number] {
  return (
    value.length >= 2 &&
    Number.isFinite(value[0]) &&
    Number.isFinite(value[1]) &&
    Math.abs(value[0] ?? 181) <= 180 &&
    Math.abs(value[1] ?? 91) <= 90
  )
}

export function getRouteMapPoints(
  catalog: RouteCatalogItem[],
): RouteMapPoint[] {
  return catalog.flatMap((item) => {
    const location =
      item.actor.locations.find(
        (candidate) => candidate.is_primary && candidate.point,
      ) ?? item.actor.locations.find((candidate) => candidate.point)
    const coordinates = location?.point?.coordinates
    if (!location || !coordinates || !validCoordinates(coordinates)) return []

    return [
      {
        actorId: item.actor.id,
        actorSlug: item.actor.slug,
        address: formatPublicAddress(location.address_fields),
        categoryName: item.actor.category_name,
        categorySlug: item.actor.category_slug,
        coordinates,
        directionsUrl: directionsHref(location),
        name: item.actor.public_name,
        summary: item.actor.short_description,
      },
    ]
  })
}

export function filterRouteMapPoints(
  points: RouteMapPoint[],
  categorySlug: string,
) {
  if (!categorySlug) return points
  return points.filter((point) => point.categorySlug === categorySlug)
}
