'use client'

import { AlertTriangle, CheckCircle2, MessageSquare, X } from 'lucide-react'
import { useState } from 'react'
import { useModalA11y } from '@econexao/ui/use-modal-a11y'

interface ReportIssueModalProps {
  isOpen: boolean
  onClose: () => void
  targetType: 'route' | 'actor' | 'general'
  targetSlug?: string
  targetName?: string
  regionSlug?: string
}

export function ReportIssueModal({
  isOpen,
  onClose,
  targetType,
  targetSlug = '',
  targetName = '',
  regionSlug = '',
}: ReportIssueModalProps) {
  const [reportType, setReportType] = useState('incorrect_info')
  const [description, setDescription] = useState('')
  const [reporterContact, setReporterContact] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const dialogRef = useModalA11y<HTMLDivElement>(isOpen, onClose)

  if (!isOpen) return null

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (description.trim().length < 10) {
      setErrorMessage(
        'Por favor, detalhe o problema com pelo menos 10 caracteres.',
      )
      return
    }

    setIsSubmitting(true)
    setErrorMessage(null)

    try {
      const res = await fetch('/api/public/reports/', {
        body: JSON.stringify({
          description: description.trim(),
          region_slug: regionSlug,
          report_type: reportType,
          reporter_contact: reporterContact.trim(),
          target_slug: targetSlug,
          target_type: targetType,
        }),
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(
          errorData.description?.[0] ||
            'Não foi possível enviar seu relato. Tente novamente.',
        )
      }

      setSuccessMessage(
        'Obrigado! Seu relato foi recebido e passará por revisão editorial antes de qualquer atualização.',
      )
      setDescription('')
      setReporterContact('')
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : 'Erro ao enviar relato. Verifique sua conexão.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div
      ref={dialogRef}
      aria-labelledby="report-modal-title"
      aria-modal="true"
      className="modal-backdrop"
      role="dialog"
      tabIndex={-1}
    >
      <div className="modal-content">
        <div className="modal-header">
          <div className="modal-title-group">
            <AlertTriangle className="icon-warning" size={20} />
            <h3 id="report-modal-title">Relatar Informação Incorreta</h3>
          </div>
          <button
            data-autofocus
            aria-label="Fechar formulário de relato"
            className="modal-close-btn"
            onClick={onClose}
            type="button"
          >
            <X size={20} />
          </button>
        </div>

        {targetName ? (
          <p className="modal-target-info">
            Referente a: <strong>{targetName}</strong>
          </p>
        ) : null}

        {successMessage ? (
          <div className="report-success-banner">
            <CheckCircle2 size={24} />
            <div>
              <p className="success-text">{successMessage}</p>
              <button className="btn-secondary" onClick={onClose} type="button">
                Concluir
              </button>
            </div>
          </div>
        ) : (
          <form className="report-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="report-type-select">Tipo de Problema</label>
              <select
                id="report-type-select"
                onChange={(e) => setReportType(e.target.value)}
                value={reportType}
              >
                <option value="incorrect_info">
                  Informação Incorreta ou Desatualizada
                </option>
                <option value="closed_location">
                  Local Fechado ou Inacessível
                </option>
                <option value="wrong_contact">
                  Contato ou Telefone Errado
                </option>
                <option value="safety_warning">
                  Alerta de Segurança / Condições
                </option>
                <option value="other">Outro Assunto</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="report-description">
                Descrição Detalhada <span className="required">*</span>
              </label>
              <textarea
                id="report-description"
                maxLength={1000}
                minLength={10}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Descreva o que mudou ou precisa ser corrigido (ex: horário de funcionamento, telefone, caminho bloqueado)..."
                required
                rows={4}
                value={description}
              />
              <span className="form-help">
                Mínimo 10 caracteres (máx. 1000).
              </span>
            </div>

            <div className="form-group">
              <label htmlFor="report-contact">Seu Contato (Opcional)</label>
              <input
                id="report-contact"
                onChange={(e) => setReporterContact(e.target.value)}
                placeholder="E-mail ou telefone (caso os editores precisem esclarecer)"
                type="text"
                value={reporterContact}
              />
            </div>

            {errorMessage ? (
              <p className="form-error-banner" role="alert">
                {errorMessage}
              </p>
            ) : null}

            <p className="editorial-notice">
              <MessageSquare size={14} /> Somente editores humanos realizam
              atualizações após verificação em fontes autorizadas.
            </p>

            <div className="modal-actions">
              <button className="btn-tertiary" onClick={onClose} type="button">
                Cancelar
              </button>
              <button
                className="btn-primary"
                disabled={isSubmitting || description.trim().length < 10}
                type="submit"
              >
                {isSubmitting ? 'Enviando...' : 'Enviar Relato'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
