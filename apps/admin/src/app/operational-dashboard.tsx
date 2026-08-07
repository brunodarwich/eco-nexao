'use client'

import { useEffect, useRef, useState } from 'react'
import { FeedbackState } from '@econexao/ui/feedback-state'
import {
  AppAnalyticsView,
  CatalogItemApi,
} from './components/app-analytics-view'
import { CsvImportView } from './components/csv-import-view'
import { HeroFocus } from './components/hero-focus'
import { PoiEditorModal } from './components/poi-editor-modal'
import { SupportPointCreateModal } from './components/support-point-create-modal'
import { ReportsAlertsView } from './components/reports-alerts-view'
import { RouteReadinessView } from './components/route-readiness-view'
import {
  AdminDataState,
  AdminRequestError,
  classifyAdminResponse,
} from './components/admin-data-state'
import { DiscoveryWorkspace } from './discovery-workspace'
import {
  type PublishedRouteApiSummary,
  type RouteApiSummary,
  toDashboardRoute,
} from '../lib/dashboard-routes'
import {
  type DashboardSummaryApi,
  fetchDashboardSummary,
  getAdminRequestError,
} from '../lib/admin-api'

export interface RegionApiSummary {
  id: string
  slug: string
  public_name: string
}

export function getDashboardTabIndex(
  current: number,
  key: string,
  total: number,
): number | null {
  if (key === 'Home') return 0
  if (key === 'End') return total - 1
  if (key === 'ArrowRight' || key === 'ArrowDown') return (current + 1) % total
  if (key === 'ArrowLeft' || key === 'ArrowUp')
    return (current - 1 + total) % total
  return null
}

export function OperationalDashboard() {
  const [activeTab, setActiveTab] = useState<
    'analytics' | 'routes' | 'reports' | 'import' | 'discovery'
  >('analytics')
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([])
  const tabs = [
    'analytics',
    'routes',
    'reports',
    'import',
    'discovery',
  ] as const

  const handleTabKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    const current = tabs.indexOf(activeTab)
    const next = getDashboardTabIndex(current, event.key, tabs.length)
    if (next === null || next === current) return
    event.preventDefault()
    setActiveTab(tabs[next])
    requestAnimationFrame(() => tabRefs.current[next]?.focus())
  }

  const [regions, setRegions] = useState<RegionApiSummary[]>([])
  const [selectedRegionSlug, setSelectedRegionSlug] = useState('')
  const [regionsError, setRegionsError] = useState<AdminRequestError | null>(
    null,
  )
  const [regionsRequestKey, setRegionsRequestKey] = useState(0)
  const [regionsLoading, setRegionsLoading] = useState(true)

  const [routes, setRoutes] = useState<RouteApiSummary[]>([])
  const [selectedRouteSlug, setSelectedRouteSlug] = useState('')
  const [catalogItems, setCatalogItems] = useState<CatalogItemApi[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [routesError, setRoutesError] = useState<AdminRequestError | null>(null)
  const [catalogError, setCatalogError] = useState<AdminRequestError | null>(
    null,
  )

  const [dashboardSummary, setDashboardSummary] =
    useState<DashboardSummaryApi | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(true)
  const [summaryRequestKey, setSummaryRequestKey] = useState(0)
  const [summaryError, setSummaryError] = useState<AdminRequestError | null>(
    null,
  )

  // Estado do Modal de Edição Manual
  const [isEditorModalOpen, setIsEditorModalOpen] = useState(false)
  const [poiToEdit, setPoiToEdit] = useState<CatalogItemApi | null>(null)

  // Estado do Modal de Cadastro Manual de Ponto de Apoio
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  // Busca lista de regiões publicadas
  useEffect(() => {
    let active = true
    fetch('/api/public/regions', { cache: 'no-store' })
      .then((res) => {
        if (!res.ok) throw classifyAdminResponse(res.status)
        return res.json()
      })
      .then((data) => {
        if (active && Array.isArray(data)) {
          setRegionsError(null)
          setRegions(data)
          setSelectedRegionSlug((prev) =>
            data.some((r) => r.slug === prev) ? prev : data[0]?.slug || '',
          )
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setRegions([])
          setSelectedRegionSlug('')
          setRegionsError(
            typeof error === 'string'
              ? (error as AdminRequestError)
              : 'unavailable',
          )
        }
      })
      .finally(() => {
        if (active) setRegionsLoading(false)
      })
    return () => {
      active = false
    }
  }, [regionsRequestKey])

  // Busca rotas da região selecionada
  useEffect(() => {
    if (!selectedRegionSlug) {
      return
    }
    let active = true
    fetch(`/api/public/regions/${selectedRegionSlug}/routes`, {
      cache: 'no-store',
    })
      .then((res) => {
        if (!res.ok) throw classifyAdminResponse(res.status)
        return res.json()
      })
      .then((data) => {
        if (active) {
          setRoutesError(null)
          const list = Array.isArray(data)
            ? (data as PublishedRouteApiSummary[]).map(toDashboardRoute)
            : []
          setRoutes(list)
          if (list.length > 0) {
            setSelectedRouteSlug(list[0].slug)
          } else {
            setSelectedRouteSlug('')
            setCatalogItems([])
          }
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setRoutes([])
          setSelectedRouteSlug('')
          setCatalogItems([])
          setRoutesError(
            typeof error === 'string'
              ? (error as AdminRequestError)
              : 'unavailable',
          )
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
      .then((res) => {
        if (!res.ok) throw classifyAdminResponse(res.status)
        return res.json()
      })
      .then((data) => {
        if (active) {
          setCatalogError(null)
          setCatalogItems(Array.isArray(data) ? data : [])
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setCatalogItems([])
          setCatalogError(
            typeof error === 'string'
              ? (error as AdminRequestError)
              : 'unavailable',
          )
        }
      })

    return () => {
      active = false
    }
  }, [selectedRegionSlug, selectedRouteSlug])

  // Busca resumo operacional para o Hero (contadores reais por região)
  useEffect(() => {
    if (!selectedRegionSlug) return

    let active = true
    fetchDashboardSummary(selectedRegionSlug)
      .then((data) => {
        if (active) {
          setSummaryLoading(false)
          setSummaryError(null)
          setDashboardSummary(data)
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setSummaryLoading(false)
          setDashboardSummary(null)
          setSummaryError(getAdminRequestError(err))
        }
      })

    return () => {
      active = false
    }
  }, [selectedRegionSlug, summaryRequestKey])

  function handleOpenEditorModal(itemToEdit: CatalogItemApi) {
    setPoiToEdit(itemToEdit)
    setIsEditorModalOpen(true)
  }

  function handleSavePoi(savedPoi: CatalogItemApi) {
    setCatalogItems((prev) => {
      const existsIndex = prev.findIndex(
        (item) => item.actor?.id === savedPoi.actor?.id,
      )
      if (existsIndex >= 0) {
        const next = [...prev]
        next[existsIndex] = savedPoi
        return next
      }
      return prev
    })
  }

  const selectedRegion = regions.find((r) => r.slug === selectedRegionSlug)
  const selectedRegionName =
    selectedRegion?.public_name ||
    selectedRegionSlug ||
    'Nenhuma região selecionada'
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
            disabled={
              regionsLoading || Boolean(regionsError) || !regions.length
            }
            value={selectedRegionSlug}
            onChange={(e) => {
              setIsLoading(true)
              setSummaryLoading(true)
              setSummaryError(null)
              setSelectedRegionSlug(e.target.value)
            }}
          >
            {regions.map((r) => (
              <option key={r.slug} value={r.slug}>
                {r.public_name}
              </option>
            ))}
          </select>
        </div>

        <div className="region-info-tag">
          <span>Multirregional:</span>
          <strong>Eixo Ativo</strong>
        </div>
      </div>

      {regionsLoading ? (
        <FeedbackState
          message="Buscando as regiões disponíveis para a operação..."
          title="Carregando regiões"
          variant="loading"
        />
      ) : regionsError ? (
        <AdminDataState
          error={regionsError}
          onRetry={() => {
            setRegionsLoading(true)
            setRegionsRequestKey((value) => value + 1)
          }}
        />
      ) : !regions.length ? (
        <AdminDataState
          error="unavailable"
          onRetry={() => {
            setRegionsLoading(true)
            setRegionsRequestKey((value) => value + 1)
          }}
        />
      ) : null}

      {summaryError ? (
        <AdminDataState
          error={summaryError}
          onRetry={() => {
            setSummaryLoading(true)
            setSummaryRequestKey((value) => value + 1)
          }}
        />
      ) : (
        <HeroFocus
          activeRouteName={selectedRouteName}
          alertsCount={
            summaryLoading || !dashboardSummary
              ? null
              : dashboardSummary.active_alerts_count
          }
          onNavigateTab={setActiveTab}
          pendingRevisionsCount={
            summaryLoading || !dashboardSummary
              ? null
              : dashboardSummary.pending_revisions_count
          }
          regionName={selectedRegionName}
          routeCount={routes.length}
        />
      )}

      <nav
        aria-label="Navegação do Painel Operacional"
        className="dashboard-tabs"
        role="tablist"
      >
        <button
          aria-controls="dashboard-tabpanel-analytics"
          aria-selected={activeTab === 'analytics'}
          className={`tab-button ${activeTab === 'analytics' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('analytics')}
          onKeyDown={handleTabKeyDown}
          ref={(element) => {
            tabRefs.current[0] = element
          }}
          role="tab"
          tabIndex={activeTab === 'analytics' ? 0 : -1}
          id="dashboard-tab-analytics"
          type="button"
        >
          📊 Métricas do App
        </button>

        <button
          aria-controls="dashboard-tabpanel-routes"
          aria-selected={activeTab === 'routes'}
          className={`tab-button ${activeTab === 'routes' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('routes')}
          onKeyDown={handleTabKeyDown}
          ref={(element) => {
            tabRefs.current[1] = element
          }}
          role="tab"
          tabIndex={activeTab === 'routes' ? 0 : -1}
          id="dashboard-tab-routes"
          type="button"
        >
          🗺️ Rotas & Prontidão ({routes.length})
        </button>

        <button
          aria-controls="dashboard-tabpanel-reports"
          aria-selected={activeTab === 'reports'}
          className={`tab-button ${activeTab === 'reports' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('reports')}
          onKeyDown={handleTabKeyDown}
          ref={(element) => {
            tabRefs.current[2] = element
          }}
          role="tab"
          tabIndex={activeTab === 'reports' ? 0 : -1}
          id="dashboard-tab-reports"
          type="button"
        >
          🔔 Relatos & Auditoria
        </button>

        <button
          aria-controls="dashboard-tabpanel-import"
          aria-selected={activeTab === 'import'}
          className={`tab-button ${activeTab === 'import' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('import')}
          onKeyDown={handleTabKeyDown}
          ref={(element) => {
            tabRefs.current[3] = element
          }}
          role="tab"
          tabIndex={activeTab === 'import' ? 0 : -1}
          id="dashboard-tab-import"
          type="button"
        >
          📥 Importar CSV
        </button>

        <button
          aria-controls="dashboard-tabpanel-discovery"
          aria-selected={activeTab === 'discovery'}
          className={`tab-button ${activeTab === 'discovery' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('discovery')}
          onKeyDown={handleTabKeyDown}
          ref={(element) => {
            tabRefs.current[4] = element
          }}
          role="tab"
          tabIndex={activeTab === 'discovery' ? 0 : -1}
          id="dashboard-tab-discovery"
          type="button"
        >
          🔍 Descoberta Externa (Google Places)
        </button>
      </nav>

      <div
        aria-labelledby={`dashboard-tab-${activeTab}`}
        className="tab-content-panel"
        id={`dashboard-tabpanel-${activeTab}`}
        role="tabpanel"
        tabIndex={0}
      >
        {activeTab === 'analytics' && (
          <AppAnalyticsView
            catalogItems={catalogItems}
            isLoading={isLoading}
            requestError={routesError ?? catalogError}
            onOpenCreateModal={() => setIsCreateModalOpen(true)}
            onOpenEditorModal={handleOpenEditorModal}
            onSelectRoute={setSelectedRouteSlug}
            regionSlug={selectedRegionSlug}
            routes={routes}
            selectedRouteSlug={selectedRouteSlug}
          />
        )}

        {activeTab === 'routes' && (
          <RouteReadinessView regionSlug={selectedRegionSlug} />
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
        regionId={selectedRegion?.id || ''}
        routeSlug={selectedRouteSlug}
      />

      <SupportPointCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSave={() => setIsCreateModalOpen(false)}
        regionId={selectedRegion?.id || ''}
        regionSlug={selectedRegionSlug}
        routes={routes}
        selectedRouteSlug={selectedRouteSlug}
      />
    </div>
  )
}
