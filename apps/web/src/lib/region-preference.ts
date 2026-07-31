import type { RegionSummary } from './public-api'

export const REGION_PREFERENCE_KEY = 'econexao:region:v1'

export function readRegionPreference() {
  try {
    return window.localStorage.getItem(REGION_PREFERENCE_KEY)
  } catch {
    return null
  }
}

export function saveRegionPreference(slug: string) {
  try {
    window.localStorage.setItem(REGION_PREFERENCE_KEY, slug)
  } catch {
    // A navegação pública continua disponível quando o armazenamento é bloqueado.
  }
}

export function clearRegionPreference() {
  try {
    window.localStorage.removeItem(REGION_PREFERENCE_KEY)
  } catch {
    // Armazenamento indisponível
  }
}

export function resolvePreferredRegion(
  regions: RegionSummary[],
  storedSlug: string | null,
) {
  if (!storedSlug) {
    return null
  }

  return regions.find((region) => region.slug === storedSlug) ?? null
}

