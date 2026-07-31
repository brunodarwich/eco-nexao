import type { OfflinePackageMetadata } from './offline-storage'

export function buildRoutePackageResources(
  regionSlug: string,
  routeSlug: string,
) {
  const encodedRegion = encodeURIComponent(regionSlug)
  const encodedRoute = encodeURIComponent(routeSlug)
  const pageBase = `/${encodedRegion}/rotas/${encodedRoute}`
  const apiBase = `/api/public/regions/${encodedRegion}/routes/${encodedRoute}`
  return [
    pageBase,
    `${pageBase}/mapa`,
    `${pageBase}/catalogo`,
    apiBase,
    `${apiBase}/catalog`,
  ]
}

export async function cacheRoutePackage(
  routeKey: string,
  version: string,
  resources: string[],
): Promise<OfflinePackageMetadata> {
  if (!('serviceWorker' in navigator) || !('caches' in window)) {
    throw new Error('Seu navegador não oferece suporte ao conteúdo offline.')
  }

  const cacheName = `econexao-route:${encodeURIComponent(routeKey)}:${encodeURIComponent(version)}:${Date.now()}`
  const temporaryName = `${cacheName}:temporary`
  const pending = [...resources]
  const cachedResources = new Set<string>()
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 60_000)
  let sizeBytes = 0

  await window.caches.delete(temporaryName)
  const temporaryCache = await window.caches.open(temporaryName)

  try {
    while (pending.length > 0) {
      const resource = pending.shift()
      if (!resource || cachedResources.has(resource)) continue
      const response = await fetch(resource, {
        cache: 'reload',
        signal: controller.signal,
      })
      if (!response.ok) {
        throw new Error('Um recurso essencial da rota está indisponível.')
      }
      const html = response.headers.get('content-type')?.includes('text/html')
        ? await response.clone().text()
        : ''
      sizeBytes += (await response.clone().arrayBuffer()).byteLength
      await temporaryCache.put(resource, response)
      cachedResources.add(resource)

      if (html) {
        for (const match of html.matchAll(
          /(?:src|href)=["']([^"']*\/_next\/static\/[^"']+)["']/g,
        )) {
          const assetUrl = new URL(match[1], window.location.origin)
          if (assetUrl.origin === window.location.origin) {
            pending.push(`${assetUrl.pathname}${assetUrl.search}`)
          }
        }
      }
    }

    const finalCache = await window.caches.open(cacheName)
    for (const request of await temporaryCache.keys()) {
      const response = await temporaryCache.match(request)
      if (response) await finalCache.put(request, response)
    }
    await navigator.serviceWorker.register('/sw.js')
    await navigator.serviceWorker.ready
    await waitForServiceWorkerControl()
  } catch (error) {
    await window.caches.delete(cacheName)
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('O download offline demorou mais que o esperado.')
    }
    throw error
  } finally {
    window.clearTimeout(timeout)
    await window.caches.delete(temporaryName)
  }

  return {
    cacheName,
    downloadedAt: new Date().toISOString(),
    resourceCount: cachedResources.size,
    routeKey,
    sizeBytes,
    version,
  }
}

async function waitForServiceWorkerControl() {
  if (navigator.serviceWorker.controller) return
  await new Promise<void>((resolve, reject) => {
    const timeout = window.setTimeout(() => {
      navigator.serviceWorker.removeEventListener('controllerchange', onChange)
      reject(new Error('O recurso offline ainda não assumiu esta página.'))
    }, 10_000)
    function onChange() {
      window.clearTimeout(timeout)
      resolve()
    }
    navigator.serviceWorker.addEventListener('controllerchange', onChange, {
      once: true,
    })
  })
}

export async function deleteRoutePackage(cacheName: string) {
  if (!('caches' in window)) return
  await window.caches.delete(cacheName)
}
