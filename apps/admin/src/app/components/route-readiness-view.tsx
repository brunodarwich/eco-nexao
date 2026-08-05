'use client'

import { useEffect, useState } from 'react'
import { FeedbackState } from '@econexao/ui/feedback-state'
import type { components } from '@econexao/contracts/api'
import { adminRequest, getAdminRequestError } from '../../lib/admin-api'
import { AdminDataState, type AdminRequestError } from './admin-data-state'

export type RouteReadinessDto = components['schemas']['RouteReadiness']
type ReadinessResponse = components['schemas']['RegionRouteReadinessResponse']

const statusLabels: Record<string, string> = {
  approved: 'Aprovado',
  archived: 'Arquivado',
  draft: 'Rascunho',
  published: 'Publicado',
  review: 'Em Revisão',
  suspended: 'Suspenso',
}

const reasonLabels: Record<string, string> = {
  active_critical_alert: 'Existe alerta crítico vigente.',
  missing_segments: 'O traçado não possui segmentos.',
  missing_stages: 'A rota não possui etapas.',
  unverified_public_contact: 'Existe contato público sem verificação.',
}

function reasonLabel(reason: string) {
  if (reason.startsWith('missing_required_field:')) {
    return `Campo obrigatório ausente: ${reason.split(':')[1]}.`
  }
  return reasonLabels[reason] ?? reason
}

export function RouteReadinessMatrix({
  regionSlug,
  routes,
}: {
  regionSlug: string
  routes: RouteReadinessDto[]
}) {
  if (!routes.length) {
    return (
      <FeedbackState
        message={`Nenhuma rota encontrada para a região "${regionSlug}".`}
        title="Matriz sem dados"
        variant="empty"
      />
    )
  }

  return (
    <div className="readiness-workspace">
      <header className="readiness-header">
        <h2>Matriz de Prontidão e Estado Editorial</h2>
        <p className="readiness-subtitle">
          Fórmula auditável por conteúdo, traçado, catálogo, alertas e offline.
        </p>
      </header>
      <div className="readiness-table-container">
        <table className="readiness-table">
          <thead>
            <tr>
              <th>Rota</th>
              <th>Estado</th>
              <th>Dimensões</th>
              <th>Catálogo</th>
              <th>Revisão</th>
              <th>Prontidão</th>
            </tr>
          </thead>
          <tbody>
            {routes.map((route) => {
              const status =
                statusLabels[route.editorial_status] ?? route.editorial_status
              const statusClass =
                route.editorial_status === 'published'
                  ? 'status--published'
                  : route.editorial_status === 'review'
                    ? 'status--review'
                    : 'status--draft'
              return (
                <tr key={route.route_id}>
                  <td>
                    <strong>{route.title}</strong>
                    <span className="route-slug-text">{route.slug}</span>
                  </td>
                  <td>
                    <span className={`status-badge ${statusClass}`}>
                      {status}
                    </span>
                    <small>
                      Versão {route.published_version ?? 'não publicada'}
                    </small>
                  </td>
                  <td>
                    <span>Conteúdo {route.dimensions.content}%</span>
                    <br />
                    <span>Traçado {route.dimensions.trace}%</span>
                    <br />
                    <span>Alertas {route.dimensions.alerts}%</span>
                    <br />
                    <span>Offline {route.dimensions.offline}%</span>
                  </td>
                  <td>
                    <span>{route.published_points_count} publicados</span>
                    <br />
                    <span>{route.points_in_review_count} em revisão</span>
                    <br />
                    <span>
                      {route.verified_contacts_count} contatos verificados
                    </span>
                  </td>
                  <td>
                    {route.last_revision_at
                      ? new Date(route.last_revision_at).toLocaleDateString(
                          'pt-BR',
                        )
                      : 'Sem revisão registrada'}
                  </td>
                  <td>
                    <strong>
                      {route.score === null
                        ? 'Indisponível'
                        : `${route.score}%`}
                    </strong>
                    <span>{route.is_ready ? 'Pronta' : 'Não pronta'}</span>
                    {route.blocking_reasons.length ? (
                      <ul
                        aria-label={`Motivos de não prontidão de ${route.title}`}
                      >
                        {route.blocking_reasons.map((reason) => (
                          <li key={reason}>{reasonLabel(reason)}</li>
                        ))}
                      </ul>
                    ) : null}
                    <small>Fórmula {route.formula_version}</small>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function RouteReadinessView({ regionSlug }: { regionSlug: string }) {
  const [data, setData] = useState<ReadinessResponse | null>(null)
  const [error, setError] = useState<AdminRequestError | null>(null)
  const [requestKey, setRequestKey] = useState(0)

  useEffect(() => {
    let active = true
    adminRequest<ReadinessResponse>(
      `routes/readiness?region_slug=${encodeURIComponent(regionSlug)}`,
    )
      .then((response) => {
        if (active) {
          setData(response)
          setError(null)
        }
      })
      .catch((requestError: unknown) => {
        if (active) setError(getAdminRequestError(requestError))
      })
    return () => {
      active = false
    }
  }, [regionSlug, requestKey])

  if (error) {
    return (
      <AdminDataState
        error={error}
        onRetry={() => setRequestKey((value) => value + 1)}
      />
    )
  }
  if (!data || data.region_slug !== regionSlug) {
    return (
      <FeedbackState
        message="Consultando indicadores administrativos auditáveis..."
        title="Carregando matriz de prontidão"
        variant="loading"
      />
    )
  }
  return (
    <RouteReadinessMatrix regionSlug={data.region_slug} routes={data.routes} />
  )
}
