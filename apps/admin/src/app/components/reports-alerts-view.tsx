'use client'

import { FeedbackState } from '@econexao/ui/feedback-state'
import { useEffect, useState } from 'react'

export interface AuditEventItem {
  id: string
  action: string
  actor_username?: string
  entity_type?: string
  result?: string
  created_at?: string
  reason?: string
}

interface ReportsAlertsViewProps {
  regionSlug: string
}

export function ReportsAlertsView({ regionSlug }: ReportsAlertsViewProps) {
  const [events, setEvents] = useState<AuditEventItem[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true
    fetch('/api/admin/audit-logs', {
      cache: 'no-store',
      credentials: 'include',
    })
      .then((res) => {
        if (!res.ok)
          throw new Error(
            'Não foi possível carregar os registros de auditoria.',
          )
        return res.json()
      })
      .then((data) => {
        if (active) {
          const results = Array.isArray(data) ? data : data.results || []
          setEvents(results)
        }
      })
      .catch(() => {
        if (active) setEvents([])
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  if (isLoading) {
    return (
      <FeedbackState
        message="Consultando a central de relatos e auditoria em tempo real..."
        title="Carregando relatos"
        variant="loading"
      />
    )
  }

  return (
    <div className="reports-workspace">
      <div className="reports-header">
        <div>
          <h2>Central de Relatos e Alertas da Comunidade</h2>
          <p className="reports-subtitle">
            Avisos de segurança, solicitações de atualização de contatos e
            histórico de auditoria em {regionSlug}.
          </p>
        </div>
      </div>

      {events.length ? (
        <ul className="reports-list">
          {events.map((event) => (
            <li className="report-card" key={event.id}>
              <div className="report-card-header">
                <span className="report-severity-badge">
                  Ação: {event.action}
                </span>
                <span className="report-date">
                  {event.created_at
                    ? new Date(event.created_at).toLocaleString('pt-BR')
                    : 'Data recente'}
                </span>
              </div>
              <div className="report-card-body">
                <h4>Entidade: {event.entity_type || 'Registro do Sistema'}</h4>
                <p>
                  Operador: <strong>{event.actor_username || 'Sistema'}</strong>{' '}
                  • Resultado: {event.result || 'OK'}
                </p>
                {event.reason ? (
                  <p className="report-reason">Motivo: {event.reason}</p>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <FeedbackState
          message={`Nenhum alerta de segurança ou relato de visitante pendente de triagem em "${regionSlug}".`}
          title="Nenhum relato pendente"
          variant="empty"
        />
      )}
    </div>
  )
}
