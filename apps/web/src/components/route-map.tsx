'use client'

import { Button } from '@econexao/ui/button'
import { ChevronDown, ChevronUp, Layers, Locate, Maximize2 } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { RouteCatalogItem, RouteDetail } from '@/lib/public-api'
import {
  filterRouteMapPoints,
  getRouteMapPoints,
  type RouteMapPoint,
} from '@/lib/route-map-points'
import { useModalA11y } from '@econexao/ui/use-modal-a11y'

interface RouteMapProps {
  catalog: RouteCatalogItem[]
  route: RouteDetail
}

type LocationState =
  'idle' | 'explaining' | 'locating' | 'visible' | 'denied' | 'unavailable'

const mapStyleUrl =
  process.env.NEXT_PUBLIC_MAP_STYLE_URL ??
  'https://demotiles.maplibre.org/style.json'

function actorFeatureCollection(points: RouteMapPoint[]) {
  return {
    features: points.map((point) => ({
      geometry: { coordinates: point.coordinates, type: 'Point' as const },
      properties: {
        actorId: point.actorId,
        actorSlug: point.actorSlug,
        address: point.address,
        categoryName: point.categoryName,
        name: point.name,
        summary: point.summary,
      },
      type: 'Feature' as const,
    })),
    type: 'FeatureCollection' as const,
  }
}

function addPopupContent(
  point: RouteMapPoint,
  route: RouteDetail,
): HTMLDivElement {
  const root = document.createElement('div')
  root.className = 'route-map-popup'

  const category = document.createElement('span')
  category.className = 'route-map-popup__category'
  category.textContent = point.categoryName
  root.append(category)

  const title = document.createElement('strong')
  title.textContent = point.name
  root.append(title)

  if (point.address) {
    const address = document.createElement('span')
    address.textContent = point.address
    root.append(address)
  }

  const actions = document.createElement('div')
  actions.className = 'route-map-popup__actions'
  const detail = document.createElement('a')
  detail.href = `/${route.region_slug}/rotas/${route.slug}/catalogo?ator=${encodeURIComponent(point.actorSlug)}`
  detail.textContent = 'Ver detalhes'
  actions.append(detail)

  if (point.directionsUrl) {
    const directions = document.createElement('a')
    directions.href = point.directionsUrl
    directions.rel = 'noreferrer'
    directions.target = '_blank'
    directions.textContent = 'Como chegar'
    actions.append(directions)
  }
  root.append(actions)
  return root
}

export function RouteMap({ catalog, route }: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<import('maplibre-gl').Map | null>(null)
  const locationMarkerRef = useRef<import('maplibre-gl').Marker | null>(null)
  const visiblePointsRef = useRef<RouteMapPoint[]>([])
  const [activeCategory, setActiveCategory] = useState('')
  const [locationState, setLocationState] = useState<LocationState>('idle')
  const locationDialogRef = useModalA11y<HTMLDivElement>(
    locationState === 'explaining',
    () => setLocationState('idle'),
  )
  const [mapMessage, setMapMessage] = useState('')
  const allPoints = useMemo(() => getRouteMapPoints(catalog), [catalog])
  const visiblePoints = useMemo(
    () => filterRouteMapPoints(allPoints, activeCategory),
    [activeCategory, allPoints],
  )
  const categories = useMemo(
    () =>
      Array.from(
        new Map(
          allPoints.map((point) => [point.categorySlug, point.categoryName]),
        ),
      ).sort((left, right) => left[1].localeCompare(right[1], 'pt-BR')),
    [allPoints],
  )

  useEffect(() => {
    visiblePointsRef.current = visiblePoints
    const source = mapRef.current?.getSource('route-actors') as
      import('maplibre-gl').GeoJSONSource | undefined
    source?.setData(actorFeatureCollection(visiblePoints))
  }, [visiblePoints])

  useEffect(() => {
    const container = containerRef.current
    const stageCoordinates = route.stages.map(
      (stage) => stage.point.coordinates as [number, number],
    )
    const initialCoordinates = [
      ...stageCoordinates,
      ...allPoints.map((point) => point.coordinates),
    ]
    if (!container || initialCoordinates.length === 0) return
    let disposed = false
    let themeObserver: MutationObserver | null = null

    void import('maplibre-gl')
      .then((maplibre) => {
        if (disposed) return

        const bounds = initialCoordinates.reduce(
          (currentBounds, coordinate) => currentBounds.extend(coordinate),
          new maplibre.LngLatBounds(
            initialCoordinates[0],
            initialCoordinates[0],
          ),
        )
        const map = new maplibre.Map({
          bounds,
          container,
          fitBoundsOptions: { padding: 56 },
          style: mapStyleUrl,
        })
        mapRef.current = map
        map.addControl(
          new maplibre.NavigationControl({ showCompass: false }),
          'top-right',
        )

        const applyTheme = () => {
          const styles = getComputedStyle(document.documentElement)
          const primary = styles.getPropertyValue('--color-primary').trim()
          const accent = styles.getPropertyValue('--color-accent').trim()
          if (map.getLayer('route-line')) {
            map.setPaintProperty('route-line', 'line-color', primary)
          }
          if (map.getLayer('route-stages')) {
            map.setPaintProperty('route-stages', 'circle-color', accent)
            map.setPaintProperty('route-stages', 'circle-stroke-color', primary)
          }
          if (map.getLayer('actor-clusters')) {
            map.setPaintProperty('actor-clusters', 'circle-color', primary)
          }
          if (map.getLayer('actor-points')) {
            map.setPaintProperty('actor-points', 'circle-color', primary)
            map.setPaintProperty('actor-points', 'circle-stroke-color', accent)
          }
        }

        map.on('load', () => {
          const styles = getComputedStyle(document.documentElement)
          const primary = styles.getPropertyValue('--color-primary').trim()
          const accent = styles.getPropertyValue('--color-accent').trim()
          map.addSource('route-segments', {
            data: {
              features: route.segments.map((segment) => ({
                geometry: segment.geometry,
                properties: { id: segment.id },
                type: 'Feature' as const,
              })),
              type: 'FeatureCollection' as const,
            },
            type: 'geojson',
          })
          map.addLayer({
            id: 'route-line',
            paint: { 'line-color': primary, 'line-width': 5 },
            source: 'route-segments',
            type: 'line',
          })
          map.addSource('route-actors', {
            cluster: true,
            clusterMaxZoom: 14,
            clusterRadius: 48,
            data: actorFeatureCollection(visiblePointsRef.current),
            type: 'geojson',
          })
          map.addLayer({
            filter: ['has', 'point_count'],
            id: 'actor-clusters',
            paint: {
              'circle-color': primary,
              'circle-radius': [
                'step',
                ['get', 'point_count'],
                18,
                20,
                24,
                75,
                30,
              ],
              'circle-stroke-color': accent,
              'circle-stroke-width': 3,
            },
            source: 'route-actors',
            type: 'circle',
          })
          map.addLayer({
            filter: ['has', 'point_count'],
            id: 'actor-cluster-count',
            layout: {
              'text-field': ['get', 'point_count_abbreviated'],
              'text-size': 13,
            },
            paint: {
              'text-color': styles
                .getPropertyValue('--color-on-primary')
                .trim(),
            },
            source: 'route-actors',
            type: 'symbol',
          })
          map.addLayer({
            filter: ['!', ['has', 'point_count']],
            id: 'actor-points',
            paint: {
              'circle-color': primary,
              'circle-radius': 7,
              'circle-stroke-color': accent,
              'circle-stroke-width': 3,
            },
            source: 'route-actors',
            type: 'circle',
          })
          map.addSource('route-stage-points', {
            data: {
              features: route.stages.map((stage) => ({
                geometry: stage.point,
                properties: { name: `${stage.position}. ${stage.public_name}` },
                type: 'Feature' as const,
              })),
              type: 'FeatureCollection' as const,
            },
            type: 'geojson',
          })
          map.addLayer({
            id: 'route-stages',
            paint: {
              'circle-color': accent,
              'circle-radius': 9,
              'circle-stroke-color': primary,
              'circle-stroke-width': 3,
            },
            source: 'route-stage-points',
            type: 'circle',
          })
          map.moveLayer('actor-clusters')
          map.moveLayer('actor-cluster-count')
          map.moveLayer('actor-points')

          map.on('click', 'actor-clusters', async (event) => {
            const feature = event.features?.[0]
            if (!feature) return
            const clusterId = feature?.properties?.cluster_id
            if (typeof clusterId !== 'number') return
            const source = map.getSource(
              'route-actors',
            ) as import('maplibre-gl').GeoJSONSource
            const zoom = await source.getClusterExpansionZoom(clusterId)
            if (feature.geometry.type !== 'Point') return
            map.easeTo({
              center: feature.geometry.coordinates as [number, number],
              zoom,
            })
          })
          map.on('click', 'actor-points', (event) => {
            const feature = event.features?.[0]
            if (feature?.geometry.type !== 'Point') return
            const actorId = feature.properties?.actorId
            const point = visiblePointsRef.current.find(
              (candidate) => candidate.actorId === actorId,
            )
            if (!point) return
            new maplibre.Popup({ closeButton: true })
              .setLngLat(feature.geometry.coordinates as [number, number])
              .setDOMContent(addPopupContent(point, route))
              .addTo(map)
          })
          map.on('click', 'route-stages', (event) => {
            const actorAtPoint = map.queryRenderedFeatures(event.point, {
              layers: ['actor-points'],
            })
            if (actorAtPoint.length > 0) return
            const feature = event.features?.[0]
            const coordinates =
              feature?.geometry.type === 'Point'
                ? (feature.geometry.coordinates as [number, number])
                : null
            const name = feature?.properties?.name
            if (!coordinates || typeof name !== 'string') return
            new maplibre.Popup({ closeButton: true })
              .setLngLat(coordinates)
              .setText(name)
              .addTo(map)
          })
          for (const layer of [
            'actor-clusters',
            'actor-points',
            'route-stages',
          ]) {
            map.on('mouseenter', layer, () => {
              map.getCanvas().style.cursor = 'pointer'
            })
            map.on('mouseleave', layer, () => {
              map.getCanvas().style.cursor = ''
            })
          }
          applyTheme()
          themeObserver = new MutationObserver(applyTheme)
          themeObserver.observe(document.documentElement, {
            attributeFilter: ['data-theme'],
            attributes: true,
          })
        })
        map.on('error', () => {
          setMapMessage(
            'O mapa base encontrou uma falha. A lista completa continua disponível abaixo.',
          )
        })
      })
      .catch(() => {
        setMapMessage(
          'O mapa não pôde ser iniciado. Use a lista textual e os links externos.',
        )
      })

    return () => {
      disposed = true
      themeObserver?.disconnect()
      locationMarkerRef.current?.remove()
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [allPoints, route])

  function requestLocation() {
    if (!navigator.geolocation) {
      setLocationState('unavailable')
      return
    }

    setLocationState('locating')
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const map = mapRef.current
        if (!map) {
          setLocationState('unavailable')
          return
        }

        void import('maplibre-gl').then((maplibre) => {
          const coordinates: [number, number] = [
            position.coords.longitude,
            position.coords.latitude,
          ]
          locationMarkerRef.current?.remove()
          locationMarkerRef.current = new maplibre.Marker({
            color: getComputedStyle(document.documentElement)
              .getPropertyValue('--color-primary')
              .trim(),
          })
            .setLngLat(coordinates)
            .addTo(map)
          map.flyTo({ center: coordinates, maxDuration: 800, zoom: 14 })
          setLocationState('visible')
        })
      },
      (error) => {
        setLocationState(
          error.code === error.PERMISSION_DENIED ? 'denied' : 'unavailable',
        )
      },
      { enableHighAccuracy: false, maximumAge: 60_000, timeout: 8_000 },
    )
  }

  function fitCoordinates(coordinates: [number, number][]) {
    const map = mapRef.current
    if (!map || coordinates.length === 0) return
    void import('maplibre-gl').then((maplibre) => {
      const bounds = coordinates.reduce(
        (currentBounds, coordinate) => currentBounds.extend(coordinate),
        new maplibre.LngLatBounds(coordinates[0], coordinates[0]),
      )
      map.fitBounds(bounds, { maxDuration: 800, padding: 56 })
    })
  }

  const [isSheetExpanded, setIsSheetExpanded] = useState(false)

  function centerRoute() {
    fitCoordinates(
      route.stages.map((stage) => stage.point.coordinates as [number, number]),
    )
  }

  function showVisiblePoints() {
    fitCoordinates(visiblePoints.map((point) => point.coordinates))
  }

  return (
    <section aria-labelledby="route-map-title" className="route-map-container">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Mapa da rota</p>
          <h2 id="route-map-title">Percurso, etapas e pontos locais</h2>
        </div>
        <span aria-live="polite">
          {visiblePoints.length}{' '}
          {visiblePoints.length === 1 ? 'ponto publicado' : 'pontos publicados'}
        </span>
      </div>

      {categories.length > 0 ? (
        <div
          aria-label="Filtrar pontos por categoria"
          className="map-category-filters"
        >
          <button
            aria-pressed={!activeCategory}
            onClick={() => setActiveCategory('')}
            type="button"
          >
            Todos <span>{allPoints.length}</span>
          </button>
          {categories.map(([slug, name]) => {
            const count = allPoints.filter(
              (point) => point.categorySlug === slug,
            ).length
            return (
              <button
                aria-pressed={activeCategory === slug}
                key={slug}
                onClick={() => setActiveCategory(slug)}
                type="button"
              >
                {name} <span>{count}</span>
              </button>
            )
          })}
        </div>
      ) : (
        <p className="map-empty-note" role="status">
          Ainda não há pontos locais publicados nesta rota. O percurso e as
          etapas continuam disponíveis; novos pontos aparecerão aqui após
          revisão editorial.
        </p>
      )}

      <div className="map-actions">
        <Button onClick={centerRoute} type="button" variant="secondary">
          <Maximize2 aria-hidden="true" />
          <span>Centralizar no percurso</span>
        </Button>
        {visiblePoints.length > 0 ? (
          <Button onClick={showVisiblePoints} type="button" variant="secondary">
            <Layers aria-hidden="true" />
            <span>Ver pontos filtrados</span>
          </Button>
        ) : null}
        <Button
          onClick={() => setLocationState('explaining')}
          type="button"
          variant="secondary"
        >
          <Locate aria-hidden="true" />
          <span>Usar minha localização</span>
        </Button>
      </div>

      {locationState === 'explaining' ? (
        <div
          ref={locationDialogRef}
          aria-labelledby="location-title"
          aria-modal="true"
          className="location-consent"
          role="dialog"
          tabIndex={-1}
        >
          <h3 id="location-title">Usar sua posição somente neste aparelho?</h3>
          <p>
            A posição será desenhada localmente para ajudar na orientação. Ela
            não será enviada à ECOnexão, ao analytics ou aos nossos servidores.
          </p>
          <div className="map-actions">
            <Button data-autofocus onClick={requestLocation}>
              Continuar
            </Button>
            <Button
              onClick={() => setLocationState('idle')}
              type="button"
              variant="secondary"
            >
              Agora não
            </Button>
          </div>
        </div>
      ) : null}

      {locationState === 'locating' ? (
        <p aria-live="polite">Consultando a localização do aparelho…</p>
      ) : null}
      {locationState === 'visible' ? (
        <p aria-live="polite">Sua posição está visível somente neste mapa.</p>
      ) : null}
      {locationState === 'denied' ? (
        <p role="status">
          Localização não autorizada. O mapa e a lista continuam disponíveis.
        </p>
      ) : null}
      {locationState === 'unavailable' ? (
        <p role="status">
          Não foi possível obter sua localização. Continue usando o mapa ou a
          lista.
        </p>
      ) : null}

      {mapMessage ? (
        <p className="map-message" role="status">
          {mapMessage}
        </p>
      ) : null}

      <div className="route-map-wrapper">
        <div
          aria-label={`Mapa da rota ${route.public_name}`}
          className="route-map-canvas"
          ref={containerRef}
          role="region"
        />

        <div className="map-overlay-controls">
          <button
            aria-label="Centralizar no percurso"
            className="map-overlay-button"
            onClick={centerRoute}
            type="button"
          >
            <Maximize2 aria-hidden="true" />
          </button>
          <button
            aria-label="Centralizar mapa na minha localização"
            className="map-overlay-button"
            onClick={() => setLocationState('explaining')}
            type="button"
          >
            <Locate aria-hidden="true" />
          </button>
        </div>

        <div
          className={`map-bottom-sheet${
            isSheetExpanded ? ' map-bottom-sheet--expanded' : ''
          }`}
        >
          <button
            aria-expanded={isSheetExpanded}
            aria-label={
              isSheetExpanded
                ? 'Recolher resumo de etapas do mapa'
                : 'Expandir resumo de etapas do mapa'
            }
            className="map-sheet-handle-button"
            onClick={() => setIsSheetExpanded(!isSheetExpanded)}
            type="button"
          >
            <span aria-hidden="true" className="map-sheet-handle" />
            <div className="map-sheet-summary">
              <strong>{route.public_name}</strong>
              <span>
                {route.stages.length} etapas • {visiblePoints.length} pontos
              </span>
            </div>
            {isSheetExpanded ? (
              <ChevronDown aria-hidden="true" />
            ) : (
              <ChevronUp aria-hidden="true" />
            )}
          </button>

          {isSheetExpanded ? (
            <div className="map-sheet-content">
              <h4>Etapas do percurso</h4>
              <ol className="stage-list">
                {route.stages.map((stage) => (
                  <li key={stage.id}>
                    <div>
                      <strong>
                        {stage.position}. {stage.public_name}
                      </strong>
                      {stage.description ? <p>{stage.description}</p> : null}
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          ) : null}
        </div>
      </div>

      <div className="map-list-alternative">
        <h3>Lista equivalente ao mapa</h3>
        <section
          aria-labelledby="published-points-title"
          className="map-points-list"
        >
          <div className="section-heading section-heading--compact">
            <h4 id="published-points-title">Pontos locais publicados</h4>
            <span>{visiblePoints.length}</span>
          </div>
          {visiblePoints.length > 0 ? (
            <ul className="stage-list">
              {visiblePoints.map((point) => (
                <li key={point.actorId}>
                  <div>
                    <span className="map-point-category">
                      {point.categoryName}
                    </span>
                    <strong>{point.name}</strong>
                    <p>{point.summary}</p>
                    {point.address ? (
                      <p className="muted-text">{point.address}</p>
                    ) : null}
                  </div>
                  <div className="map-point-actions">
                    <a
                      href={`/${route.region_slug}/rotas/${route.slug}/catalogo?ator=${encodeURIComponent(point.actorSlug)}`}
                    >
                      Detalhes
                    </a>
                    {point.directionsUrl ? (
                      <a
                        href={point.directionsUrl}
                        rel="noreferrer"
                        target="_blank"
                      >
                        Como chegar
                      </a>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p>Nenhum ponto publicado corresponde ao filtro atual.</p>
          )}
        </section>

        <section aria-labelledby="route-stages-list-title">
          <h4 id="route-stages-list-title">Etapas do percurso</h4>
          <ol className="stage-list">
            {route.stages.map((stage) => {
              const [longitude, latitude] = stage.point.coordinates
              return (
                <li key={stage.id}>
                  <div>
                    <strong>
                      {stage.position}. {stage.public_name}
                    </strong>
                    <p>{stage.description}</p>
                    <p>{stage.arrival_guidance}</p>
                  </div>
                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`}
                    rel="noreferrer"
                    target="_blank"
                  >
                    Como chegar
                  </a>
                </li>
              )
            })}
          </ol>
        </section>
      </div>
    </section>
  )
}
