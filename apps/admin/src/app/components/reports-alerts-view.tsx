'use client'

import { FeedbackState } from '@econexao/ui/feedback-state'
import { useEffect, useState } from 'react'
import {
  AdminDataState,
  AdminRequestError,
  classifyAdminResponse,
} from './admin-data-state'

export interface AuditEventItem {
  id: string
  action: string
  actor_username?: string
  entity_type?: string
  result?: string
  created_at?: string
  reason?: string
}

export interface PublicReportItem {
  id: string
  report_type: string
  target_type: string
  target_slug?: string
  region_slug?: string
  description: string
  reporter_contact?: string
  status: 'pending' | 'reviewed' | 'rejected' | 'actioned'
  moderation_note?: string
  created_at?: string
}

interface ReportsAlertsViewProps {
  regionSlug: string
}

export function ReportsAlertsView({ regionSlug }: ReportsAlertsViewProps) {
  const [reports, setReports] = useState<PublicReportItem[]>([])
  const [events, setEvents] = useState<AuditEventItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [requestError, setRequestError] = useState<AdminRequestError | null>(
    null,
  )

  useEffect(() => {
    let active = true

    const fetchJson = async (url: string) => {
      const res = await fetch(url, {
        cache: 'no-store',
        credentials: 'include',
      })
      if (!res.ok) throw classifyAdminResponse(res.status)
      return res.json()
    }

    Promise.allSettled([
      fetchJson('/api/admin/reports/'),
      fetchJson('/api/admin/audit-logs'),
    ]).then(([reportsRes, auditRes]) => {
      if (!active) return
      const failed = [reportsRes, auditRes].find(
        (result) => result.status === 'rejected',
      )
      if (failed?.status === 'rejected') {
        setRequestError(
          typeof failed.reason === 'string'
            ? (failed.reason as AdminRequestError)
            : 'unavailable',
        )
      } else {
        setRequestError(null)
      }
      if (
        reportsRes.status === 'fulfilled' &&
        Array.isArray(reportsRes.value)
      ) {
        setReports(reportsRes.value)
      }
      if (auditRes.status === 'fulfilled') {
        const data = auditRes.value
        setEvents(Array.isArray(data) ? data : data.results || [])
      }
      setIsLoading(false)
    })

    return () => {
      active = false
    }
  }, [regionSlug])

  async function handleModerate(reportId: string, newStatus: string) {
    try {
      const csrfRes = await fetch('/api/admin/auth/csrf', {
        credentials: 'include',
      })
      const csrfData = await csrfRes.json().catch(() => ({}))
      const csrfToken = csrfData.csrf_token || ''

      const res = await fetch(`/api/admin/reports/${reportId}/`, {
        body: JSON.stringify({
          moderation_note: `Moderado no painel em ${new Date().toLocaleString('pt-BR')}`,
          status: newStatus,
        }),
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        method: 'PATCH',
      })
      if (res.ok) {
        setReports((prev) =>
          prev.map((item) =>
            item.id === reportId
              ? { ...item, status: newStatus as PublicReportItem['status'] }
              : item,
          ),
        )
      }
    } catch {
      // Graceful fallback
    }
  }

  if (isLoading) {
    return (
      <FeedbackState
        message="Consultando a central de relatos e auditoria em tempo real..."
        title="Carregando relatos"
        variant="loading"
      />
    )
  }

  if (requestError) {
    return <AdminDataState error={requestError} />
  }

  const pendingReports = reports.filter((r) => r.status === 'pending')

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

      {reports.length ? (
        <div className="reports-section">
          <h3>Relatos de Visitantes ({pendingReports.length} pendentes)</h3>
          <ul className="reports-list">
            {reports.map((report) => (
              <li className="report-card" key={report.id}>
                <div className="report-card-header">
                  <span
                    className={`report-severity-badge status-${report.status}`}
                  >
                    {report.report_type} • Status: {report.status}
                  </span>
                  <span className="report-date">
                    {report.created_at
                      ? new Date(report.created_at).toLocaleString('pt-BR')
                      : 'Data recente'}
                  </span>
                </div>
                <div className="report-card-body">
                  <h4>
                    Alvo: {report.target_type} ({report.target_slug || 'Geral'})
                  </h4>
                  <p className="report-reason">
                    Descrição: {report.description}
                  </p>
                  {report.reporter_contact ? (
                    <p className="report-contact">
                      Contato do visitante: {report.reporter_contact}
                    </p>
                  ) : null}
                  {report.moderation_note ? (
                    <p className="report-note">
                      Nota técnica: {report.moderation_note}
                    </p>
                  ) : null}

                  {report.status === 'pending' ? (
                    <div
                      className="report-actions"
                      style={{
                        display: 'flex',
                        gap: '0.5rem',
                        marginTop: '0.75rem',
                      }}
                    >
                      <button
                        className="btn-secondary"
                        onClick={() => handleModerate(report.id, 'reviewed')}
                        type="button"
                      >
                        Marcar Revisado
                      </button>
                      <button
                        className="btn-tertiary"
                        onClick={() => handleModerate(report.id, 'rejected')}
                        type="button"
                      >
                        Rejeitar
                      </button>
                    </div>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {events.length ? (
        <div className="audit-section" style={{ marginTop: '2rem' }}>
          <h3>Histórico de Auditoria do Sistema</h3>
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
                  <h4>
                    Entidade: {event.entity_type || 'Registro do Sistema'}
                  </h4>
                  <p>
                    Operador:{' '}
                    <strong>{event.actor_username || 'Sistema'}</strong> •
                    Resultado: {event.result || 'OK'}
                  </p>
                  {event.reason ? (
                    <p className="report-reason">Motivo: {event.reason}</p>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!reports.length && !events.length ? (
        <FeedbackState
          message={`Nenhum alerta de segurança ou relato de visitante pendente de triagem em "${regionSlug}".`}
          title="Nenhum relato pendente"
          variant="empty"
        />
      ) : null}
    </div>
  )
}
