'use client'

import { Button } from '@econexao/ui/button'
import { Download, Heart } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { RouteDetail } from '@/lib/public-api'
import {
  cacheRoutePackage,
  buildRoutePackageResources,
  deleteRoutePackage,
} from '@/lib/offline-package'
import {
  formatPackageSize,
  getOfflinePackage,
  isFavorite,
  isOfflinePackageOutdated,
  removeOfflinePackageMetadata,
  routeStorageKey,
  saveOfflinePackage,
  setFavorite,
  type OfflinePackageMetadata,
} from '@/lib/offline-storage'
import { trackEvent } from '@/lib/analytics-sdk'

const favoriteChangedEvent = 'econexao:favorite-changed'

export function RouteFavoriteButton({
  className = '',
  compact = false,
  route,
}: {
  className?: string
  compact?: boolean
  route: RouteDetail
}) {
  const routeKey = routeStorageKey(route.region_slug, route.slug)
  const [favorite, setFavoriteState] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    function syncFavorite() {
      setFavoriteState(isFavorite(window.localStorage, routeKey))
    }

    const timeout = window.setTimeout(syncFavorite, 0)
    window.addEventListener(favoriteChangedEvent, syncFavorite)
    window.addEventListener('storage', syncFavorite)
    return () => {
      window.clearTimeout(timeout)
      window.removeEventListener(favoriteChangedEvent, syncFavorite)
      window.removeEventListener('storage', syncFavorite)
    }
  }, [routeKey])

  function toggleFavorite() {
    const next = !favorite
    try {
      setFavorite(window.localStorage, routeKey, next)
      setFavoriteState(next)
      window.dispatchEvent(new Event(favoriteChangedEvent))
      setMessage(
        next
          ? 'Rota adicionada aos favoritos.'
          : 'Rota removida dos favoritos.',
      )
    } catch {
      setMessage('Não foi possível salvar o favorito neste dispositivo.')
    }
  }

  const label = favorite ? 'Remover dos favoritos' : 'Favoritar rota'

  return (
    <>
      <Button
        aria-label={compact ? `${label} na barra superior` : label}
        aria-pressed={favorite}
        className={className}
        onClick={toggleFavorite}
        title={compact ? label : undefined}
        type="button"
        variant="secondary"
      >
        <Heart
          aria-hidden="true"
          className="route-local-action__icon"
          fill={favorite ? 'currentColor' : 'none'}
        />
        {compact ? (
          <span className="sr-only">{label}</span>
        ) : favorite ? (
          'Favorita'
        ) : (
          'Favoritar'
        )}
      </Button>
      <span aria-live="polite" className="sr-only">
        {message}
      </span>
    </>
  )
}

export function RouteLocalActions({ route }: { route: RouteDetail }) {
  const routeKey = routeStorageKey(route.region_slug, route.slug)
  const [offlinePackage, setOfflinePackage] =
    useState<OfflinePackageMetadata | null>(null)
  const [confirmingDownload, setConfirmingDownload] = useState(false)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setOfflinePackage(getOfflinePackage(window.localStorage, routeKey))
    }, 0)
    return () => window.clearTimeout(timeout)
  }, [routeKey])

  const packageOutdated = isOfflinePackageOutdated(
    offlinePackage,
    route.updated_at,
  )

  async function download() {
    setBusy(true)
    setMessage('Preparando o conteúdo offline…')
    try {
      const resources = buildRoutePackageResources(
        route.region_slug,
        route.slug,
      )
      const metadata = await cacheRoutePackage(
        routeKey,
        route.updated_at,
        resources,
      )
      try {
        saveOfflinePackage(window.localStorage, metadata)
      } catch {
        await deleteRoutePackage(metadata.cacheName)
        throw new Error(
          'O armazenamento local deste dispositivo está indisponível.',
        )
      }
      if (offlinePackage && offlinePackage.cacheName !== metadata.cacheName) {
        void deleteRoutePackage(offlinePackage.cacheName)
      }
      setOfflinePackage(metadata)
      void trackEvent('offline_download_completed', {
        region_id: route.region_slug,
        route_id: route.slug,
      })
      setConfirmingDownload(false)
      setMessage(
        `Rota salva para uso offline: ${formatPackageSize(metadata.sizeBytes)}.`,
      )
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Não foi possível salvar a rota offline.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function removePackage() {
    if (!offlinePackage) return
    setBusy(true)
    try {
      await deleteRoutePackage(offlinePackage.cacheName)
      removeOfflinePackageMetadata(window.localStorage, routeKey)
      setOfflinePackage(null)
      setMessage('Conteúdo offline removido deste dispositivo.')
    } catch {
      setMessage('Não foi possível remover o conteúdo offline.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section
      aria-label="Preferências locais da rota"
      className="route-local-actions"
    >
      <div className="route-local-actions__buttons">
        {route.offline_enabled ? (
          <Button
            className="route-local-action"
            disabled={busy}
            onClick={() => setConfirmingDownload(true)}
            type="button"
            variant="secondary"
          >
            <Download aria-hidden="true" className="route-local-action__icon" />
            {offlinePackage
              ? packageOutdated
                ? 'Atualizar conteúdo offline'
                : 'Baixar novamente'
              : 'Salvar offline'}
          </Button>
        ) : null}
        <RouteFavoriteButton className="route-local-action" route={route} />
        {offlinePackage ? (
          <Button
            disabled={busy}
            onClick={() => void removePackage()}
            type="button"
            variant="secondary"
          >
            Remover conteúdo offline
          </Button>
        ) : null}
      </div>

      {packageOutdated ? (
        <p className="offline-warning">
          Há uma versão mais recente desta rota. Atualize o conteúdo antes de
          sair.
        </p>
      ) : null}

      {confirmingDownload ? (
        <div className="offline-confirmation">
          <strong>
            {offlinePackage
              ? 'Substituir o pacote offline?'
              : 'Salvar esta rota offline?'}
          </strong>
          <p>
            Inclui resumo, preparação, etapas, alertas e catálogo essencial. O
            tamanho será calculado durante o download.
          </p>
          <p>
            Não inclui tiles do mapa, sua localização nem conteúdo de fontes
            externas.
          </p>
          <div className="route-local-actions__buttons">
            <Button
              disabled={busy}
              onClick={() => void download()}
              type="button"
            >
              {busy ? 'Salvando…' : 'Confirmar download'}
            </Button>
            <Button
              disabled={busy}
              onClick={() => setConfirmingDownload(false)}
              type="button"
              variant="secondary"
            >
              Cancelar
            </Button>
          </div>
        </div>
      ) : null}

      {offlinePackage && !packageOutdated ? (
        <p className="verification-note">
          Disponível offline · {formatPackageSize(offlinePackage.sizeBytes)} ·{' '}
          {offlinePackage.resourceCount} recursos.
        </p>
      ) : null}
      <p aria-live="polite" className="sr-only">
        {message}
      </p>
      {message ? <p className="local-action-message">{message}</p> : null}
    </section>
  )
}
