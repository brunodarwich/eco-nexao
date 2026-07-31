'use client'

import { FeedbackState } from '@econexao/ui/feedback-state'
import { RouteApiSummary } from './app-analytics-view'

interface RouteReadinessViewProps {
  regionSlug: string
  routes: RouteApiSummary[]
  isLoading: boolean
}

export function RouteReadinessView({
  regionSlug,
  routes,
  isLoading,
}: RouteReadinessViewProps) {
  if (isLoading) {
    return (
      <FeedbackState
        message="Consultando a matriz de prontidão das rotas em..."
        title="Carregando matriz de prontidão"
        variant="loading"
      />
    )
  }

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
      <div className="readiness-header">
        <div>
          <h2>Matriz de Prontidão e Estado Editorial</h2>
          <p className="readiness-subtitle">
            Acompanhe o grau de prontidão de cada dimensão antes da publicação
            no aplicativo ECOnexão.
          </p>
        </div>
      </div>

      <div className="readiness-table-container">
        <table className="readiness-table">
          <thead>
            <tr>
              <th>Rota</th>
              <th>Status Editorial</th>
              <th>Conteúdo</th>
              <th>Traçado / GPX</th>
              <th>Catálogo de Apoio</th>
              <th>Prontidão Geral</th>
            </tr>
          </thead>
          <tbody>
            {routes.map((route) => {
              const hasTitle = Boolean(route.title)
              const hasSummary = Boolean(route.summary)
              const contentScore = (hasTitle ? 50 : 0) + (hasSummary ? 50 : 0)

              const stages = route.stages_count || 0
              const distance = route.distance_km || 0
              const gpxScore = (stages > 0 ? 50 : 0) + (distance > 0 ? 50 : 0)

              const actors = route.actors_count || 0
              const catalogScore = Math.min(100, actors * 25)

              const overallScore = Math.round(
                (contentScore + gpxScore + catalogScore) / 3,
              )

              const status = route.editorial_status || 'Publicado'
              const statusClass =
                status === 'Publicado'
                  ? 'status--published'
                  : status === 'Em Revisão'
                    ? 'status--review'
                    : 'status--draft'

              return (
                <tr key={route.slug}>
                  <td>
                    <div className="route-name-cell">
                      <strong>{route.title}</strong>
                      <span className="route-slug-text">{route.slug}</span>
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge ${statusClass}`}>
                      {status}
                    </span>
                  </td>
                  <td>
                    <span className="score-pill">{contentScore}%</span>
                  </td>
                  <td>
                    <span className="score-pill">
                      {stages} estágio(s) • {distance} km
                    </span>
                  </td>
                  <td>
                    <span className="score-pill">{actors} ponto(s)</span>
                  </td>
                  <td>
                    <div className="overall-score-cell">
                      <strong>{overallScore}%</strong>
                      <div className="readiness-progress-track">
                        <div
                          className="readiness-progress-fill"
                          style={{ width: `${overallScore}%` }}
                        />
                      </div>
                    </div>
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
