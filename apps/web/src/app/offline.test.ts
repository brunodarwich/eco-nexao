import { describe, expect, it } from 'vitest'
import { buildRoutePackageResources } from '../lib/offline-package'
import {
  formatPackageSize,
  getOfflinePackage,
  isFavorite,
  isOfflinePackageOutdated,
  removeOfflinePackageMetadata,
  saveOfflinePackage,
  setFavorite,
} from '../lib/offline-storage'

function memoryStorage() {
  const values = new Map<string, string>()
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
  }
}

describe('estado local e pacote offline', () => {
  it('persiste favoritos sem conta', () => {
    const storage = memoryStorage()
    setFavorite(storage, 'regiao/rota', true)
    expect(isFavorite(storage, 'regiao/rota')).toBe(true)
    setFavorite(storage, 'regiao/rota', false)
    expect(isFavorite(storage, 'regiao/rota')).toBe(false)
  })

  it('ignora dados locais corrompidos', () => {
    const storage = {
      getItem: () => '{inválido',
      setItem: () => undefined,
    }
    expect(isFavorite(storage, 'regiao/rota')).toBe(false)
    expect(getOfflinePackage(storage, 'regiao/rota')).toBeNull()
  })

  it('salva e remove metadados do pacote por rota', () => {
    const storage = memoryStorage()
    const metadata = {
      cacheName: 'cache-v1',
      downloadedAt: '2026-07-29T12:00:00Z',
      resourceCount: 5,
      routeKey: 'regiao/rota',
      sizeBytes: 2048,
      version: 'v1',
    }
    saveOfflinePackage(storage, metadata)
    expect(getOfflinePackage(storage, 'regiao/rota')).toEqual(metadata)
    removeOfflinePackageMetadata(storage, 'regiao/rota')
    expect(getOfflinePackage(storage, 'regiao/rota')).toBeNull()
  })

  it('identifica pacote vencido pela versão editorial da rota', () => {
    const metadata = {
      cacheName: 'cache-v1',
      downloadedAt: '2026-07-29T12:00:00Z',
      resourceCount: 5,
      routeKey: 'regiao/rota',
      sizeBytes: 2048,
      version: 'v1',
    }

    expect(isOfflinePackageOutdated(metadata, 'v1')).toBe(false)
    expect(isOfflinePackageOutdated(metadata, 'v2')).toBe(true)
    expect(isOfflinePackageOutdated(null, 'v2')).toBe(false)
  })

  it('gera somente recursos essenciais same-origin', () => {
    const resources = buildRoutePackageResources('região-a', 'rota-1')

    expect(resources).toEqual([
      '/regi%C3%A3o-a/rotas/rota-1',
      '/regi%C3%A3o-a/rotas/rota-1/mapa',
      '/regi%C3%A3o-a/rotas/rota-1/catalogo',
      '/api/public/regions/regi%C3%A3o-a/routes/rota-1',
      '/api/public/regions/regi%C3%A3o-a/routes/rota-1/catalog',
    ])
    expect(resources.every((resource) => resource.startsWith('/'))).toBe(true)
    expect(
      resources.every(
        (resource) =>
          !resource.includes('google') && !resource.includes('external'),
      ),
    ).toBe(true)
    expect(formatPackageSize(2048)).toBe('2 KB')
  })
})
