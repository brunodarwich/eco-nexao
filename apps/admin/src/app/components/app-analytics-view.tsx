'use client'

import { Button } from '@econexao/ui/button'
import { FeedbackState } from '@econexao/ui/feedback-state'

export interface RouteApiSummary {
  slug: string
  title: string
  summary?: string
  distance_km?: number
  estimated_minutes?: number
  stages_count?: number
  actors_count?: number
  editorial_status?: string
}

export interface CatalogItemApi {
  id?: string
  editorial_status?: string
  actor?: {
    id: string
    display_name: string
    category?: {
      name: string
      slug: string
    }
  }
  public_locations?: Array<{
    formatted_address?: string
    locality?: string
  }>
  public_contact_channels?: Array<{
    channel_type: string
    public_value: string
  }>
}

interface AppAnalyticsViewProps {
  regionSlug: string
  routes: RouteApiSummary[]
  selectedRouteSlug: string
  catalogItems: CatalogItemApi[]
  isLoading: boolean
  onSelectRoute: (slug: string) => void
  onOpenEditorModal: (itemToEdit?: CatalogItemApi | null) => void
}

export function AppAnalyticsView({
  regionSlug,
  routes,
  selectedRouteSlug,
  catalogItems,
  isLoading,
  onSelectRoute,
  onOpenEditorModal,
}: AppAnalyticsViewProps) {
  if (isLoading) {
    return (
      <FeedbackState
        message="Buscando informações da região e do catálogo publicado..."
        title="Carregando dados do aplicativo"
        variant="loading"
      />
    )
  }

  if (!routes.length) {
    return (
      <FeedbackState
        message={`Não foram encontradas rotas publicadas para a região "${regionSlug}". Cadastre rotas no sistema para visualizar métricas do aplicativo.`}
        title="Nenhuma rota disponível"
        variant="empty"
      />
    )
  }

  const selectedRoute =
    routes.find((r) => r.slug === selectedRouteSlug) || routes[0]

  const totalStages = routes.reduce((acc, r) => acc + (r.stages_count || 0), 0)
  const totalActors = routes.reduce((acc, r) => acc + (r.actors_count || 0), 0)

  return (
    <div className="analytics-workspace">
      <div className="kpi-grid">
        <article className="kpi-card">
          <span className="kpi-icon">🗺️</span>
          <div className="kpi-body">
            <span className="kpi-label">Rotas Ativas</span>
            <span className="kpi-value">{routes.length}</span>
            <span className="kpi-subtext">em {regionSlug}</span>
          </div>
        </article>

        <article className="kpi-card">
          <span className="kpi-icon">📍</span>
          <div className="kpi-body">
            <span className="kpi-label">Estágios Mapeados</span>
            <span className="kpi-value">{totalStages}</span>
            <span className="kpi-subtext">trechos de rota</span>
          </div>
        </article>

        <article className="kpi-card">
          <span className="kpi-icon">🏪</span>
          <div className="kpi-body">
            <span className="kpi-label">Pontos de Apoio</span>
            <span className="kpi-value">
              {catalogItems.length || totalActors}
            </span>
            <span className="kpi-subtext">atores no catálogo</span>
          </div>
        </article>

        <article className="kpi-card">
          <span className="kpi-icon">📲</span>
          <div className="kpi-body">
            <span className="kpi-label">Modo Offline</span>
            <span className="kpi-value">Pronto</span>
            <span className="kpi-subtext">pacotes sincronizados</span>
          </div>
        </article>
      </div>

      <div className="analytics-main-grid">
        <section className="routes-selector-panel">
          <h3>Selecione a Rota para Análise</h3>
          <p className="panel-hint">
            Escolha uma rota para inspecionar os pontos de apoio e contatos mais
            acessados.
          </p>
          <ul className="route-list">
            {routes.map((route) => {
              const isSelected = route.slug === selectedRoute?.slug
              return (
                <li key={route.slug}>
                  <button
                    className={`route-item-button ${isSelected ? 'is-selected' : ''}`}
                    onClick={() => onSelectRoute(route.slug)}
                    type="button"
                  >
                    <div className="route-item-header">
                      <strong>{route.title}</strong>
                      <span className="route-status-tag">
                        {route.editorial_status || 'Publicada'}
                      </span>
                    </div>
                    <p className="route-item-details">
                      {route.distance_km
                        ? `${route.distance_km} km`
                        : 'Extensão N/I'}{' '}
                      • {route.stages_count || 0} estágio(s) •{' '}
                      {route.actors_count || 0} ponto(s)
                    </p>
                  </button>
                </li>
              )
            })}
          </ul>
        </section>

        <section className="poi-analytics-panel">
          <div className="panel-header">
            <div>
              <h3>Pontos de Apoio e Interação no App</h3>
              <p className="panel-hint">
                Rota selecionada: <strong>{selectedRoute?.title}</strong>
              </p>
            </div>
            <div className="panel-actions-group">
              <Button onClick={() => onOpenEditorModal(null)} type="button">
                + Adicionar Ponto Manual
              </Button>
            </div>
          </div>

          {catalogItems.length ? (
            <ul className="poi-analytics-list">
              {catalogItems.map((item, index) => {
                const name =
                  item.actor?.display_name || `Ponto de Apoio #${index + 1}`
                const category =
                  item.actor?.category?.name || 'Serviço Turístico'
                const address =
                  item.public_locations?.[0]?.formatted_address ||
                  item.public_locations?.[0]?.locality ||
                  'Endereço verificado em mapa'
                const contactsCount = item.public_contact_channels?.length || 0

                const hasAddress = Boolean(item.public_locations?.length)
                const hasContacts = contactsCount > 0
                const completenessScore =
                  (hasAddress ? 50 : 0) + (hasContacts ? 50 : 0)

                return (
                  <li className="poi-card" key={item.id || index}>
                    <div className="poi-info">
                      <div className="poi-title-row">
                        <h4>{name}</h4>
                        <div className="poi-badge-action-row">
                          <span className="poi-category">{category}</span>
                          <button
                            className="poi-edit-button"
                            onClick={() => onOpenEditorModal(item)}
                            type="button"
                          >
                            ✏️ Editar
                          </button>
                        </div>
                      </div>
                      <p className="poi-address">📍 {address}</p>
                      <p className="poi-contacts">
                        📞 {contactsCount} canal(is) de contato público
                        autorizados
                      </p>
                    </div>

                    <div className="poi-metric-bar-container">
                      <div className="poi-metric-label">
                        <span>Prontidão de Exibição</span>
                        <strong>{completenessScore}%</strong>
                      </div>
                      <div className="poi-progress-track">
                        <div
                          className="poi-progress-fill"
                          style={{ width: `${completenessScore}%` }}
                        />
                      </div>
                    </div>
                  </li>
                )
              })}
            </ul>
          ) : (
            <FeedbackState
              message={`Não há pontos de apoio cadastrados no catálogo para a rota "${selectedRoute?.title}".`}
              title="Nenhum ponto vinculado"
              variant="empty"
            />
          )}
        </section>
      </div>
    </div>
  )
}
