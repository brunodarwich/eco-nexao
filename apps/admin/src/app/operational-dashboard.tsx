'use client'

import { useEffect, useState } from 'react'
import {
  AppAnalyticsView,
  CatalogItemApi,
  RouteApiSummary,
} from './components/app-analytics-view'
import { CsvImportView } from './components/csv-import-view'
import { HeroFocus } from './components/hero-focus'
import { PoiEditorModal } from './components/poi-editor-modal'
import { ReportsAlertsView } from './components/reports-alerts-view'
import { RouteReadinessView } from './components/route-readiness-view'
import { DiscoveryWorkspace } from './discovery-workspace'

export interface RegionApiSummary {
  id?: string
  slug: string
  name: string
}

export function OperationalDashboard() {
  const [activeTab, setActiveTab] = useState<
    'analytics' | 'routes' | 'reports' | 'import' | 'discovery'
  >('analytics')

  const [regions, setRegions] = useState<RegionApiSummary[]>([
    { slug: 'santarem-alter-do-chao', name: 'Santarém - Alter do Chão' },
  ])
  const [selectedRegionSlug, setSelectedRegionSlug] = useState(
    'santarem-alter-do-chao',
  )

  const [routes, setRoutes] = useState<RouteApiSummary[]>([])
  const [selectedRouteSlug, setSelectedRouteSlug] = useState('')
  const [catalogItems, setCatalogItems] = useState<CatalogItemApi[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Estado do Modal de Edição Manual
  const [isEditorModalOpen, setIsEditorModalOpen] = useState(false)
  const [poiToEdit, setPoiToEdit] = useState<CatalogItemApi | null>(null)

  // Busca lista de regiões publicadas
  useEffect(() => {
    let active = true
    fetch('/api/public/regions', { cache: 'no-store' })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (active && Array.isArray(data) && data.length > 0) {
          setRegions(data)
          setSelectedRegionSlug((prev) =>
            data.some((r) => r.slug === prev) ? prev : data[0].slug,
          )
        }
      })
      .catch(() => {})
    return () => {
      active = false
    }
  }, [])

  // Busca rotas da região selecionada
  useEffect(() => {
    let active = true
    fetch(`/api/public/regions/${selectedRegionSlug}/routes`, {
      cache: 'no-store',
    })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (active) {
          const list = Array.isArray(data) ? data : []
          setRoutes(list)
          if (list.length > 0) {
            setSelectedRouteSlug(list[0].slug)
          } else {
            setSelectedRouteSlug('')
            setCatalogItems([])
          }
        }
      })
      .catch(() => {
        if (active) {
          setRoutes([])
          setSelectedRouteSlug('')
          setCatalogItems([])
        }
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [selectedRegionSlug])

  // Busca catálogo da rota selecionada
  useEffect(() => {
    if (!selectedRouteSlug || !selectedRegionSlug) {
      return
    }

    let active = true
    fetch(
      `/api/public/regions/${selectedRegionSlug}/routes/${selectedRouteSlug}/catalog`,
      { cache: 'no-store' },
    )
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (active) {
          setCatalogItems(Array.isArray(data) ? data : [])
        }
      })
      .catch(() => {
        if (active) setCatalogItems([])
      })

    return () => {
      active = false
    }
  }, [selectedRegionSlug, selectedRouteSlug])

  function handleOpenEditorModal(itemToEdit?: CatalogItemApi | null) {
    setPoiToEdit(itemToEdit || null)
    setIsEditorModalOpen(true)
  }

  function handleSavePoi(savedPoi: CatalogItemApi) {
    setCatalogItems((prev) => {
      const existsIndex = prev.findIndex((p) => p.id === savedPoi.id)
      if (existsIndex >= 0) {
        const next = [...prev]
        next[existsIndex] = savedPoi
        return next
      }
      setRoutes((prevRoutes) =>
        prevRoutes.map((r) =>
          r.slug === selectedRouteSlug
            ? { ...r, actors_count: (r.actors_count || 0) + 1 }
            : r,
        ),
      )
      return [savedPoi, ...prev]
    })
  }

  const selectedRegionName =
    regions.find((r) => r.slug === selectedRegionSlug)?.name ||
    selectedRegionSlug
  const selectedRouteName =
    routes.find((r) => r.slug === selectedRouteSlug)?.title ||
    selectedRouteSlug ||
    'Nenhuma'

  return (
    <div className="operational-dashboard">
      <div className="region-bar">
        <div className="region-selector-group">
          <label htmlFor="region-select">Território Operacional:</label>
          <select
            id="region-select"
            value={selectedRegionSlug}
            onChange={(e) => {
              setIsLoading(true)
              setSelectedRegionSlug(e.target.value)
            }}
          >
            {regions.map((r) => (
              <option key={r.slug} value={r.slug}>
                {r.name}
              </option>
            ))}
          </select>
        </div>

        <div className="region-info-tag">
          <span>Multirregional:</span>
          <strong>Eixo Ativo</strong>
        </div>
      </div>

      <HeroFocus
        activeRouteName={selectedRouteName}
        alertsCount={0}
        onNavigateTab={setActiveTab}
        pendingRevisionsCount={0}
        regionName={selectedRegionName}
        routeCount={routes.length}
      />

      <nav
        aria-label="Navegação do Painel Operacional"
        className="dashboard-tabs"
        role="tablist"
      >
        <button
          aria-selected={activeTab === 'analytics'}
          className={`tab-button ${activeTab === 'analytics' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('analytics')}
          role="tab"
          type="button"
        >
          📊 Métricas do App
        </button>

        <button
          aria-selected={activeTab === 'routes'}
          className={`tab-button ${activeTab === 'routes' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('routes')}
          role="tab"
          type="button"
        >
          🗺️ Rotas & Prontidão ({routes.length})
        </button>

        <button
          aria-selected={activeTab === 'reports'}
          className={`tab-button ${activeTab === 'reports' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('reports')}
          role="tab"
          type="button"
        >
          🔔 Relatos & Auditoria
        </button>

        <button
          aria-selected={activeTab === 'import'}
          className={`tab-button ${activeTab === 'import' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('import')}
          role="tab"
          type="button"
        >
          📥 Importar CSV
        </button>

        <button
          aria-selected={activeTab === 'discovery'}
          className={`tab-button ${activeTab === 'discovery' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('discovery')}
          role="tab"
          type="button"
        >
          🔍 Descoberta Externa (Google Places)
        </button>
      </nav>

      <div className="tab-content-panel">
        {activeTab === 'analytics' && (
          <AppAnalyticsView
            catalogItems={catalogItems}
            isLoading={isLoading}
            onOpenEditorModal={handleOpenEditorModal}
            onSelectRoute={setSelectedRouteSlug}
            regionSlug={selectedRegionSlug}
            routes={routes}
            selectedRouteSlug={selectedRouteSlug}
          />
        )}

        {activeTab === 'routes' && (
          <RouteReadinessView
            isLoading={isLoading}
            regionSlug={selectedRegionSlug}
            routes={routes}
          />
        )}

        {activeTab === 'reports' && (
          <ReportsAlertsView regionSlug={selectedRegionSlug} />
        )}

        {activeTab === 'import' && (
          <CsvImportView
            onNavigateTab={setActiveTab}
            regionSlug={selectedRegionSlug}
            routes={routes}
            selectedRouteSlug={selectedRouteSlug}
          />
        )}

        {activeTab === 'discovery' && <DiscoveryWorkspace />}
      </div>

      <PoiEditorModal
        initialData={poiToEdit}
        isOpen={isEditorModalOpen}
        onClose={() => setIsEditorModalOpen(false)}
        onSave={handleSavePoi}
        regionSlug={selectedRegionSlug}
        routeSlug={selectedRouteSlug}
      />
    </div>
  )
}
