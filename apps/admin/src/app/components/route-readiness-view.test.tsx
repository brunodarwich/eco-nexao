import { describe, expect, it } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { AdminDataState } from './admin-data-state'
import {
  RouteReadinessMatrix,
  type RouteReadinessDto,
} from './route-readiness-view'

const readyRoute: RouteReadinessDto = {
  route_id: '00000000-0000-4000-8000-000000000001',
  slug: 'trilha-flona',
  title: 'Trilha Flona Tapajós',
  editorial_status: 'published',
  formula_version: '1.0',
  weights: { content: 30, trace: 25, catalog: 20, alerts: 15, offline: 10 },
  dimensions: {
    content: 100,
    trace: 100,
    catalog: 100,
    alerts: 100,
    offline: 100,
  },
  score: 100,
  is_ready: true,
  blocking_reasons: [],
  missing_required_fields: [],
  stages_count: 3,
  segments_count: 2,
  published_points_count: 4,
  points_in_review_count: 1,
  verified_contacts_count: 3,
  unverified_public_contacts_count: 0,
  blocking_alerts_count: 0,
  last_revision_at: '2026-08-05T12:00:00Z',
  published_version: 2,
}

describe('RouteReadinessMatrix', () => {
  it('renders an empty region without inferred rows', () => {
    const markup = renderToStaticMarkup(
      <RouteReadinessMatrix regionSlug="xingu" routes={[]} />,
    )
    expect(markup).toContain('Matriz sem dados')
    expect(markup).not.toContain('readiness-table')
  })

  it('renders real dimensions, editorial metadata and formula', () => {
    const markup = renderToStaticMarkup(
      <RouteReadinessMatrix regionSlug="tapajos" routes={[readyRoute]} />,
    )
    expect(markup).toContain('Matriz de Prontidão e Estado Editorial')
    expect(markup).toContain('Trilha Flona Tapajós')
    expect(markup).toContain('Publicado')
    expect(markup).toContain('Versão 2')
    expect(markup).toContain('Conteúdo 100%')
    expect(markup).toContain('4 publicados')
    expect(markup).toContain('1 em revisão')
    expect(markup).toContain('3 contatos verificados')
    expect(markup).toContain('Fórmula 1.0')
  })

  it('renders explicit blockers and never turns a missing score into zero', () => {
    const blocked = {
      ...readyRoute,
      score: null,
      is_ready: false,
      blocking_reasons: ['missing_stages', 'active_critical_alert'],
    }
    const markup = renderToStaticMarkup(
      <RouteReadinessMatrix regionSlug="tapajos" routes={[blocked]} />,
    )
    expect(markup).toContain('Indisponível')
    expect(markup).not.toContain('<strong>0%</strong>')
    expect(markup).toContain('A rota não possui etapas.')
    expect(markup).toContain('Existe alerta crítico vigente.')
  })

  it.each([
    ['unauthorized', 'Sessão necessária'],
    ['forbidden', 'Acesso não autorizado'],
    ['rate-limited', 'Muitas tentativas'],
    ['server-error', 'Falha no serviço'],
  ] as const)('renders %s administrative errors', (error, title) => {
    const markup = renderToStaticMarkup(<AdminDataState error={error} />)
    expect(markup).toContain(title)
  })
})
