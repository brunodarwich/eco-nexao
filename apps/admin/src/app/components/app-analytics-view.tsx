'use client'

import { useEffect, useState } from 'react'
import { FeedbackState } from '@econexao/ui/feedback-state'
import type { components } from '@econexao/contracts/api'
import {
  adminRequest,
  getAdminRequestError,
  type AdminRequestError,
} from '../../lib/admin-api'
import type { RouteApiSummary } from '../../lib/dashboard-routes'
import { AdminDataState } from './admin-data-state'

export interface CatalogItemApi {
  id?: string
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
  requestError?: AdminRequestError | null
  onSelectRoute: (slug: string) => void
  onOpenEditorModal: (itemToEdit: CatalogItemApi) => void
  onOpenCreateModal?: () => void
  operationalData?: components['schemas']['OperationalAnalyticsResponse']
}

export function AppAnalyticsView({
  regionSlug,
  routes,
  selectedRouteSlug,
  catalogItems,
  isLoading,
  requestError,
  onSelectRoute,
  onOpenEditorModal,
  onOpenCreateModal,
  operationalData,
}: AppAnalyticsViewProps) {
  const [liveEventsError, setLiveEventsError] =
    useState<AdminRequestError | null>(null)
  const [operational, setOperational] = useState<
    components['schemas']['OperationalAnalyticsResponse'] | null
  >(operationalData ?? null)

  useEffect(() => {
    async function fetchOperational() {
      try {
        const data = await adminRequest<
          components['schemas']['OperationalAnalyticsResponse']
        >(
          `analytics/operational?region_slug=${encodeURIComponent(regionSlug)}&route_slug=${encodeURIComponent(selectedRouteSlug)}`,
        )
        setOperational(data)
        setLiveEventsError(null)
      } catch (error) {
        setOperational(null)
        setLiveEventsError(getAdminRequestError(error))
      }
    }
    if (selectedRouteSlug) void fetchOperational()
  }, [regionSlug, selectedRouteSlug])

  if (requestError) {
    return <AdminDataState error={requestError} />
  }
  if (liveEventsError) {
    return <AdminDataState error={liveEventsError} />
  }

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

  return (
    <div className="analytics-workspace">
      <div className="kpi-grid">
        <article className="kpi-card">
          <span className="kpi-icon">🗺️</span>
          <div className="kpi-body">
            <span className="kpi-label">Rotas Publicadas</span>
            <span className="kpi-value">{routes.length}</span>
            <span className="kpi-subtext">em {regionSlug}</span>
          </div>
        </article>

        {[
          ['Sessões', 'session_opened', '🧭'],
          ['Rotas abertas', 'route_opened', '🗺️'],
          ['Contatos', 'contact_opened', '☎️'],
          ['Downloads', 'offline_download_completed', '⬇️'],
        ].map(([label, key, icon]) => {
          const metric = operational?.metrics.find(
            (item) => item.event_name === key,
          )
          return (
            <article className="kpi-card" key={key}>
              <span className="kpi-icon">{icon}</span>
              <div className="kpi-body">
                <span className="kpi-label">{label}</span>
                <span className="kpi-value">{metric?.count ?? '—'}</span>
                <span className="kpi-subtext">
                  {metric && !metric.suppressed
                    ? 'agregado consentido'
                    : 'indisponível ou suprimido'}
                </span>
              </div>
            </article>
          )
        })}

        <article className="kpi-card">
          <span className="kpi-icon">📍</span>
          <div className="kpi-body">
            <span className="kpi-label">Duração da Rota</span>
            <span className="kpi-value">
              {selectedRoute?.durationMinutes || '—'}
            </span>
            <span className="kpi-subtext">
              {selectedRoute?.durationMinutes
                ? 'minutos estimados'
                : 'não informada'}
            </span>
          </div>
        </article>

        <article className="kpi-card">
          <span className="kpi-icon">🏪</span>
          <div className="kpi-body">
            <span className="kpi-label">Pontos de Apoio</span>
            <span className="kpi-value">{catalogItems.length}</span>
            <span className="kpi-subtext">atores no catálogo</span>
          </div>
        </article>
      </div>

      <div className="analytics-main-grid">
        <section className="routes-selector-panel">
          <h3>Selecione a Rota</h3>
          <p className="panel-hint">
            Escolha uma rota para consultar métricas consentidas e seu catálogo
            publicado.
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
                      <span className="route-status-tag">Publicada</span>
                    </div>
                    <p className="route-item-details">
                      {route.durationMinutes
                        ? `${route.durationMinutes} minutos estimados`
                        : 'Duração não informada'}
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
              <h3>Catálogo Publicado da Rota</h3>
              <p className="panel-hint">
                Rota selecionada: <strong>{selectedRoute?.title}</strong>
              </p>
            </div>
            {onOpenCreateModal && (
              <button
                className="poi-create-button"
                onClick={onOpenCreateModal}
                type="button"
              >
                ➕ Adicionar Ponto Manual
              </button>
            )}
          </div>

          <section aria-label="Ranking de contatos por ponto de apoio">
            <h4>Ranking de contatos</h4>
            {operational?.ranking.length ? (
              <ol className="poi-analytics-list">
                {operational.ranking.map((item) => (
                  <li className="poi-card" key={item.support_point_id}>
                    <strong>{item.support_point_name}</strong>
                    <span>{item.contacts} contatos</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="panel-hint">
                Dados indisponíveis ou suprimidos para preservar a privacidade.
              </p>
            )}
          </section>

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
                        <span>Dados públicos disponíveis</span>
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
