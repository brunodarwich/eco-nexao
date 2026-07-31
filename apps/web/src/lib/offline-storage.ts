const FAVORITES_KEY = 'econexao:favorites:v1'
const OFFLINE_PACKAGES_KEY = 'econexao:offline-packages:v1'

export interface OfflinePackageMetadata {
  cacheName: string
  downloadedAt: string
  resourceCount: number
  routeKey: string
  sizeBytes: number
  version: string
}

type StorageReader = Pick<Storage, 'getItem'>
type StorageWriter = Pick<Storage, 'getItem' | 'setItem'>

function readArray(storage: StorageReader, key: string): string[] {
  try {
    const parsed: unknown = JSON.parse(storage.getItem(key) ?? '[]')
    return Array.isArray(parsed)
      ? parsed.filter((item): item is string => typeof item === 'string')
      : []
  } catch {
    return []
  }
}

function readPackages(
  storage: StorageReader,
): Record<string, OfflinePackageMetadata> {
  try {
    const parsed: unknown = JSON.parse(
      storage.getItem(OFFLINE_PACKAGES_KEY) ?? '{}',
    )
    return parsed && typeof parsed === 'object'
      ? (parsed as Record<string, OfflinePackageMetadata>)
      : {}
  } catch {
    return {}
  }
}

export function routeStorageKey(regionSlug: string, routeSlug: string) {
  return `${regionSlug}/${routeSlug}`
}

export function isFavorite(storage: StorageReader, routeKey: string) {
  return readArray(storage, FAVORITES_KEY).includes(routeKey)
}

export function setFavorite(
  storage: StorageWriter,
  routeKey: string,
  favorite: boolean,
) {
  const favorites = new Set(readArray(storage, FAVORITES_KEY))
  if (favorite) favorites.add(routeKey)
  else favorites.delete(routeKey)
  storage.setItem(FAVORITES_KEY, JSON.stringify([...favorites]))
}

export function getOfflinePackage(storage: StorageReader, routeKey: string) {
  return readPackages(storage)[routeKey] ?? null
}

export function isOfflinePackageOutdated(
  metadata: OfflinePackageMetadata | null,
  currentVersion: string,
) {
  return metadata !== null && metadata.version !== currentVersion
}

export function saveOfflinePackage(
  storage: StorageWriter,
  metadata: OfflinePackageMetadata,
) {
  const packages = readPackages(storage)
  packages[metadata.routeKey] = metadata
  storage.setItem(OFFLINE_PACKAGES_KEY, JSON.stringify(packages))
}

export function removeOfflinePackageMetadata(
  storage: StorageWriter,
  routeKey: string,
) {
  const packages = readPackages(storage)
  delete packages[routeKey]
  storage.setItem(OFFLINE_PACKAGES_KEY, JSON.stringify(packages))
}

export function formatPackageSize(sizeBytes: number) {
  if (sizeBytes <= 0) return 'tamanho calculado durante o download'
  if (sizeBytes < 1024) return `${sizeBytes} B`
  if (sizeBytes < 1024 * 1024) return `${Math.ceil(sizeBytes / 1024)} KB`
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`
}
