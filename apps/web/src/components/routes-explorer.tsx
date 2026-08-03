'use client'

import { Button } from '@econexao/ui/button'
import { FeedbackState } from '@econexao/ui/feedback-state'
import {
  Bookmark,
  Clock3,
  Gauge,
  MapPin,
  Search,
  SlidersHorizontal,
} from 'lucide-react'
import Link from 'next/link'
import { useDeferredValue, useEffect, useState } from 'react'
import {
  getPublishedRegions,
  getPublishedRoutes,
  type RegionSummary,
  type RouteSummary,
} from '@/lib/public-api'
import { saveRegionPreference } from '@/lib/region-preference'
import { filterRoutes, type RouteFilters } from '@/lib/route-filters'
import { isFavorite, routeStorageKey, setFavorite } from '@/lib/offline-storage'

interface RoutesExplorerProps {
  initialFilters: RouteFilters
  regionSlug: string
}

type LoadState = 'loading' | 'ready' | 'error'

const difficultyLabels: Record<RouteSummary['difficulty'], string> = {
  easy: 'Fácil',
  moderate: 'Moderada',
  hard: 'Difícil',
}

function formatDuration(minutes: number) {
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  if (hours === 0) {
    return `${remainingMinutes} min`
  }

  return remainingMinutes === 0
    ? `${hours} h`
    : `${hours} h ${remainingMinutes} min`
}

export function RoutesExplorer({
  initialFilters,
  regionSlug,
}: RoutesExplorerProps) {
  const [filters, setFilters] = useState(initialFilters)
  const deferredQuery = useDeferredValue(filters.query)
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [regions, setRegions] = useState<RegionSummary[]>([])
  const [routes, setRoutes] = useState<RouteSummary[]>([])
  const [favoriteRouteSlugs, setFavoriteRouteSlugs] = useState<Set<string>>(
    () => new Set(),
  )
  const [favoriteMessage, setFavoriteMessage] = useState('')
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    Promise.all([
      getPublishedRegions(controller.signal),
      getPublishedRoutes(regionSlug, controller.signal),
    ])
      .then(([publishedRegions, publishedRoutes]) => {
        setRegions(publishedRegions)
        setRoutes(publishedRoutes)
        setFavoriteRouteSlugs(
          new Set(
            publishedRoutes
              .filter((route) =>
                isFavorite(
                  window.localStorage,
                  routeStorageKey(regionSlug, route.slug),
                ),
              )
              .map((route) => route.slug),
          ),
        )
        setLoadState('ready')

        if (publishedRegions.some((region) => region.slug === regionSlug)) {
          saveRegionPreference(regionSlug)
        }
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return
        }
        setLoadState('error')
      })

    return () => controller.abort()
  }, [regionSlug, reloadKey])

  const activeRegion = regions.find((region) => region.slug === regionSlug)
  const visibleRoutes = filterRoutes(routes, {
    ...filters,
    query: deferredQuery,
  })

  function syncUrl(nextFilters: RouteFilters) {
    const params = new URLSearchParams()
    if (nextFilters.query.trim()) params.set('q', nextFilters.query.trim())
    if (nextFilters.difficulty) params.set('difficulty', nextFilters.difficulty)
    if (nextFilters.duration) params.set('duration', nextFilters.duration)
    const query = params.toString()
    window.history.replaceState(
      null,
      '',
      `/${regionSlug}/rotas${query ? `?${query}` : ''}`,
    )
  }

  function updateFilters(nextFilters: RouteFilters) {
    setFilters(nextFilters)
    syncUrl(nextFilters)
  }

  function clearFilters() {
    updateFilters({ difficulty: '', duration: '', query: '' })
  }

  function retry() {
    setLoadState('loading')
    setReloadKey((key) => key + 1)
  }

  function toggleFavorite(route: RouteSummary) {
    const isCurrentlyFavorite = favoriteRouteSlugs.has(route.slug)
    const nextFavorite = !isCurrentlyFavorite
    try {
      setFavorite(
        window.localStorage,
        routeStorageKey(regionSlug, route.slug),
        nextFavorite,
      )
      setFavoriteRouteSlugs((current) => {
        const next = new Set(current)
        if (nextFavorite) next.add(route.slug)
        else next.delete(route.slug)
        return next
      })
      setFavoriteMessage(
        nextFavorite
          ? `${route.public_name} foi adicionada aos favoritos.`
          : `${route.public_name} foi removida dos favoritos.`,
      )
    } catch {
      setFavoriteMessage(
        'Não foi possível salvar o favorito neste dispositivo.',
      )
    }
  }

  if (loadState === 'loading') {
    return (
      <FeedbackState
        message="Estamos preparando as rotas publicadas deste território."
        title="Carregando rotas"
        variant="loading"
      />
    )
  }

  if (loadState === 'error') {
    return (
      <FeedbackState
        action={<Button onClick={retry}>Tentar novamente</Button>}
        message="Sua seleção foi preservada. Verifique a conexão e tente novamente."
        title="Não foi possível carregar as rotas"
        variant="error"
      />
    )
  }

  if (!activeRegion) {
    return (
      <div className="unavailable-region">
        <FeedbackState
          action={
            <Link className="ui-button" href="/">
              Escolher outra região
            </Link>
          }
          message="Ela pode estar indisponível ou ainda não ter sido publicada."
          title="Esta região não está disponível"
          variant="empty"
        />
        {regions.length > 0 ? (
          <nav aria-label="Outras regiões publicadas">
            <h2>Regiões disponíveis</h2>
            <ul className="inline-link-list">
              {regions.map((region) => (
                <li key={region.id}>
                  <Link href={`/${region.slug}/rotas`}>
                    {region.public_name}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        ) : null}
      </div>
    )
  }

  return (
    <>
      <section className="route-heading" aria-labelledby="routes-title">
        <div className="route-heading__copy">
          <div className="route-heading__topline">
            <p className="eyebrow">Olá, explorador!</p>
            <div className="region-actions">
              <Link
                aria-label={`Trocar região. Região atual: ${activeRegion.public_name}`}
                className="region-context-chip"
                href="/"
              >
                <MapPin aria-hidden="true" />
                <span>{activeRegion.public_name}</span>
              </Link>
            </div>
          </div>
          <h1 id="routes-title">Explore o território</h1>
          <p className="hero__summary">{activeRegion.short_description}</p>
        </div>
      </section>

      <section
        aria-labelledby="filters-title"
        className="route-filters"
        role="search"
      >
        <div className="route-filters__heading">
          <h2 id="filters-title">Encontre sua próxima rota</h2>
          <span aria-live="polite">
            {visibleRoutes.length}{' '}
            {visibleRoutes.length === 1
              ? 'rota encontrada'
              : 'rotas encontradas'}
          </span>
        </div>
        <div className="route-filters__controls">
          <label className="route-filter route-filter--search">
            <span className="sr-only">Buscar rotas</span>
            <span className="route-search-control">
              <Search aria-hidden="true" />
              <input
                onChange={(event) =>
                  updateFilters({ ...filters, query: event.target.value })
                }
                placeholder="Buscar rotas e experiências"
                type="search"
                value={filters.query}
              />
            </span>
          </label>
          <div
            className={`advanced-filters${filtersExpanded ? ' advanced-filters--expanded' : ''}`}
          >
            <button
              aria-controls="advanced-route-filters"
              aria-expanded={filtersExpanded}
              aria-label="Filtros"
              className="advanced-filters__toggle"
              onClick={() => setFiltersExpanded((expanded) => !expanded)}
              type="button"
            >
              <SlidersHorizontal aria-hidden="true" />
              <span className="advanced-filters__label">Filtros</span>
            </button>
            <div
              className="advanced-filters__content"
              id="advanced-route-filters"
            >
              <label className="route-filter">
                <span>Dificuldade</span>
                <select
                  onChange={(event) =>
                    updateFilters({
                      ...filters,
                      difficulty: event.target
                        .value as RouteFilters['difficulty'],
                    })
                  }
                  value={filters.difficulty}
                >
                  <option value="">Todas</option>
                  <option value="easy">Fácil</option>
                  <option value="moderate">Moderada</option>
                  <option value="hard">Difícil</option>
                </select>
              </label>
              <label className="route-filter">
                <span>Duração</span>
                <select
                  onChange={(event) =>
                    updateFilters({
                      ...filters,
                      duration: event.target.value as RouteFilters['duration'],
                    })
                  }
                  value={filters.duration}
                >
                  <option value="">Todas</option>
                  <option value="short">Até 2 horas</option>
                  <option value="medium">De 2 a 4 horas</option>
                  <option value="long">Mais de 4 horas</option>
                </select>
              </label>
              <Button
                className="route-filters__clear"
                onClick={clearFilters}
                type="button"
                variant="secondary"
              >
                Limpar filtros
              </Button>
            </div>
          </div>
        </div>
      </section>

      <div className="featured-routes-heading">
        <div>
          <p className="eyebrow">Curadoria publicada</p>
          <h2>Rotas em destaque</h2>
        </div>
        {filters.query || filters.difficulty || filters.duration ? (
          <Button onClick={clearFilters} type="button" variant="secondary">
            Ver todas
          </Button>
        ) : (
          <span className="featured-routes-heading__count">
            {visibleRoutes.length} publicadas
          </span>
        )}
      </div>

      {visibleRoutes.length === 0 ? (
        <FeedbackState
          action={
            <Button onClick={clearFilters} variant="secondary">
              Limpar filtros
            </Button>
          }
          message="A região continua selecionada. Ajuste a busca ou remova os filtros."
          title="Nenhuma rota corresponde aos filtros"
          variant="empty"
        />
      ) : (
        <ul className="route-grid" id="routes-grid">
          {visibleRoutes.map((route) => (
            <li className="route-card" key={route.id}>
              <div className="route-card__visual">
                <span
                  aria-hidden="true"
                  className="route-card__fallback-mark"
                />
                <button
                  aria-label={
                    favoriteRouteSlugs.has(route.slug)
                      ? `Remover ${route.public_name} dos favoritos`
                      : `Favoritar ${route.public_name}`
                  }
                  aria-pressed={favoriteRouteSlugs.has(route.slug)}
                  className="route-card__favorite"
                  onClick={() => toggleFavorite(route)}
                  type="button"
                >
                  <Bookmark
                    aria-hidden="true"
                    fill={
                      favoriteRouteSlugs.has(route.slug)
                        ? 'currentColor'
                        : 'none'
                    }
                  />
                </button>
                <div className="route-card__content">
                  <h3>{route.public_name}</h3>
                  <p className="route-card__location">
                    <MapPin aria-hidden="true" />
                    {activeRegion.public_name}
                  </p>
                  <p className="route-card__promise">{route.short_promise}</p>
                  <div className="route-card__meta">
                    <span>
                      <Clock3 aria-hidden="true" />
                      {formatDuration(route.duration_minutes)}
                    </span>
                    <span>
                      <Gauge aria-hidden="true" />
                      {difficultyLabels[route.difficulty]}
                    </span>
                  </div>
                </div>
              </div>
              <Link
                aria-label={`Conhecer a rota ${route.public_name}`}
                className="route-card__link"
                href={`/${regionSlug}/rotas/${route.slug}`}
              >
                <span className="sr-only">
                  Conhecer a rota {route.public_name}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      <p aria-live="polite" className="sr-only">
        {favoriteMessage}
      </p>
    </>
  )
}
