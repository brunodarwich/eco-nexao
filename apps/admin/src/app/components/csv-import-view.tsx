'use client'

import { Button } from '@econexao/ui/button'
import { FeedbackState } from '@econexao/ui/feedback-state'
import { FormEvent, useState } from 'react'
import { adminMutation, getAdminErrorMessage } from '../../lib/admin-api'
import type { RouteApiSummary } from '../../lib/dashboard-routes'

interface CsvIssue {
  severity: 'error' | 'warning'
  code: string
  line: number
  column: string | null
  message: string
}

interface CsvPreviewRow {
  line: number
  external_id: string
  operation: 'create' | 'update' | 'archive'
}

interface CsvValidationResponse {
  valid: boolean
  sha256: string
  row_count: number
  error_count: number
  warning_count: number
  issues_truncated: boolean
  issues: CsvIssue[]
  preview: {
    create_count: number
    update_count: number
    archive_count: number
    rows: CsvPreviewRow[]
  } | null
}

interface CsvCommitResponse {
  id: string
  status: 'committed'
  replayed: boolean
  row_count: number
  warning_count: number
  create_count: number
  update_count: number
  archive_count: number
  committed_at: string
}

interface CsvImportViewProps {
  regionSlug: string
  routes: RouteApiSummary[]
  selectedRouteSlug: string
  onNavigateTab: (
    tab: 'analytics' | 'routes' | 'reports' | 'import' | 'discovery',
  ) => void
}

export function CsvImportView({
  regionSlug,
  routes,
  selectedRouteSlug,
  onNavigateTab,
}: CsvImportViewProps) {
  const [file, setFile] = useState<File | null>(null)
  const [targetRoute, setTargetRoute] = useState(
    selectedRouteSlug || routes[0]?.slug || '',
  )
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1)
  const [validation, setValidation] = useState<CsvValidationResponse | null>(
    null,
  )
  const [commit, setCommit] = useState<CsvCommitResponse | null>(null)
  const [error, setError] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [idempotencyKey, setIdempotencyKey] = useState('')

  async function handleValidate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file) return
    setError('')
    setValidation(null)
    setIsProcessing(true)
    try {
      const body = new FormData()
      body.set('file', file)
      const payload = await adminMutation<CsvValidationResponse>(
        'imports/validate',
        {
          body,
          method: 'POST',
        },
      )
      setValidation(payload)
      setIdempotencyKey(crypto.randomUUID())
      setStep(2)
    } catch (caught) {
      setError(
        getAdminErrorMessage(caught, 'A planilha não pôde ser validada.'),
      )
    } finally {
      setIsProcessing(false)
    }
  }

  async function handleCommit() {
    if (!file || !validation?.valid || !validation.preview) return
    setError('')
    setIsProcessing(true)
    try {
      const body = new FormData()
      body.set('file', file)
      body.set('sha256', validation.sha256)
      body.set('idempotency_key', idempotencyKey || crypto.randomUUID())
      body.set('confirmed', 'true')
      const payload = await adminMutation<CsvCommitResponse>('imports/commit', {
        body,
        method: 'POST',
      })
      setCommit(payload)
      setStep(4)
    } catch (caught) {
      setError(
        getAdminErrorMessage(caught, 'Os rascunhos não puderam ser gravados.'),
      )
    } finally {
      setIsProcessing(false)
    }
  }

  function handleReset() {
    setFile(null)
    setValidation(null)
    setCommit(null)
    setError('')
    setIdempotencyKey('')
    setStep(1)
  }

  const operationPreview = validation?.preview
  const canCommit = Boolean(validation?.valid && operationPreview)

  return (
    <div className="csv-import-workspace">
      <div className="csv-import-header">
        <div>
          <h2>Importação de Pontos de Apoio por CSV</h2>
          <p className="csv-import-subtitle">
            O arquivo é validado pela API administrativa. Registros confirmados
            entram somente como <strong>rascunhos privados</strong> e não
            aparecem no aplicativo antes da revisão.
          </p>
        </div>
        <a
          className="download-template-link"
          download="catalogo-template.csv"
          href="/schemas/catalogo-template.csv"
        >
          📥 Baixar Gabarito CSV
        </a>
      </div>

      <div className="csv-wizard-steps">
        <div className={`step-item ${step >= 1 ? 'is-active' : ''}`}>
          1. Seleção &amp; Envio
        </div>
        <div className={`step-item ${step >= 2 ? 'is-active' : ''}`}>
          2. Validação &amp; Prévia
        </div>
        <div className={`step-item ${step >= 3 ? 'is-active' : ''}`}>
          3. Confirmar Rascunhos
        </div>
        <div className={`step-item ${step === 4 ? 'is-active' : ''}`}>
          4. Concluído
        </div>
      </div>

      {error ? (
        <FeedbackState
          message={error}
          title="Importação interrompida"
          variant="error"
        />
      ) : null}

      {step === 1 ? (
        <section className="csv-step-card">
          <h3>Etapa 1 — Selecionar rota e CSV canônico</h3>
          <form className="form-stack" onSubmit={handleValidate}>
            <label>
              Rota de conferência
              <select
                onChange={(event) => setTargetRoute(event.target.value)}
                value={targetRoute}
              >
                {routes.map((route) => (
                  <option key={route.slug} value={route.slug}>
                    {route.title} ({route.slug})
                  </option>
                ))}
              </select>
            </label>
            <p className="panel-hint">
              Região ativa: <strong>{regionSlug}</strong>. A API também confere
              a região e a rota informadas dentro do arquivo.
            </p>
            <label>
              Arquivo CSV do catálogo *
              <input
                accept=".csv,text/csv"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                required
                type="file"
              />
            </label>
            <div className="form-actions">
              <Button isLoading={isProcessing} type="submit">
                🔍 Validar no servidor
              </Button>
            </div>
          </form>
        </section>
      ) : null}

      {step === 2 && validation ? (
        <section className="csv-step-card">
          <h3>Etapa 2 — Resultado real da validação</h3>
          <div className="csv-stats-grid">
            <div className="csv-stat-box">
              <span>Total</span>
              <strong>{validation.row_count}</strong>
            </div>
            <div className="csv-stat-box">
              <span>Erros</span>
              <strong>{validation.error_count}</strong>
            </div>
            <div className="csv-stat-box">
              <span>Avisos</span>
              <strong>{validation.warning_count}</strong>
            </div>
            <div className="csv-stat-box">
              <span>Status</span>
              <strong>{validation.valid ? 'Pronto' : 'Corrigir'}</strong>
            </div>
          </div>

          {operationPreview ? (
            <>
              <p>
                <strong>{operationPreview.create_count}</strong> criações,{' '}
                <strong>{operationPreview.update_count}</strong> atualizações e{' '}
                <strong>{operationPreview.archive_count}</strong> arquivamentos.
              </p>
              <h4>Amostra dos rascunhos:</h4>
              <ol className="candidate-list">
                {operationPreview.rows.slice(0, 12).map((row) => (
                  <li
                    className="candidate-card"
                    key={`${row.line}-${row.external_id}`}
                  >
                    <strong>{row.external_id}</strong>
                    <p>
                      Linha {row.line} • operação: {row.operation}
                    </p>
                  </li>
                ))}
              </ol>
            </>
          ) : null}

          {validation.issues.length ? (
            <>
              <h4>Erros e avisos:</h4>
              <ol className="candidate-list">
                {validation.issues.slice(0, 30).map((issue, index) => (
                  <li
                    className="candidate-card"
                    key={`${issue.line}-${issue.code}-${index}`}
                  >
                    <strong>
                      {issue.severity === 'error' ? 'Erro' : 'Aviso'} —{' '}
                      {issue.code}
                    </strong>
                    <p>
                      Linha {issue.line}
                      {issue.column ? ` • coluna ${issue.column}` : ''}:{' '}
                      {issue.message}
                    </p>
                  </li>
                ))}
              </ol>
            </>
          ) : null}

          <div className="form-actions">
            <Button onClick={handleReset} type="button" variant="secondary">
              Escolher outro arquivo
            </Button>
            {canCommit ? (
              <Button onClick={() => setStep(3)} type="button">
                Avançar para confirmação
              </Button>
            ) : null}
          </div>
        </section>
      ) : null}

      {step === 3 && validation?.preview ? (
        <section className="csv-step-card">
          <h3>Etapa 3 — Confirmar rascunhos privados</h3>
          <p className="confirm-notice">
            Serão registradas{' '}
            <strong>{validation.row_count} propostas de alteração</strong>. Esta
            ação não cria nem publica atores no catálogo público.
          </p>
          <div className="form-actions">
            <Button
              onClick={() => setStep(2)}
              type="button"
              variant="secondary"
            >
              Voltar à prévia
            </Button>
            <Button
              isLoading={isProcessing}
              onClick={handleCommit}
              type="button"
            >
              💾 Confirmar lote de rascunhos
            </Button>
          </div>
        </section>
      ) : null}

      {step === 4 && commit ? (
        <section className="csv-step-card">
          <FeedbackState
            message={`${commit.row_count} rascunhos privados registrados no lote ${commit.id}. Nenhum conteúdo foi publicado automaticamente.`}
            title={
              commit.replayed
                ? 'Lote já registrado'
                : 'Lote de rascunhos criado'
            }
            variant="empty"
          />
          <div className="form-actions">
            <Button onClick={() => onNavigateTab('reports')} type="button">
              🔔 Ver auditoria
            </Button>
            <Button onClick={handleReset} type="button" variant="secondary">
              📥 Importar outro arquivo
            </Button>
          </div>
        </section>
      ) : null}
    </div>
  )
}
