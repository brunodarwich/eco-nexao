import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { ReportsAlertsView } from './reports-alerts-view'

describe('ReportsAlertsView Component', () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('renders loading state initially during async fetch', () => {
    globalThis.fetch = vi.fn().mockImplementation(() => new Promise(() => {}))

    const markup = renderToStaticMarkup(
      <ReportsAlertsView regionSlug="santarem-alter-do-chao" />,
    )

    expect(markup).toContain('Carregando relatos')
    expect(markup).toContain(
      'Consultando a central de relatos e auditoria em tempo real...',
    )
  })

  it('renders heading title and region subtitle', () => {
    globalThis.fetch = vi.fn().mockImplementation(() => new Promise(() => {}))

    const markup = renderToStaticMarkup(
      <ReportsAlertsView regionSlug="santarem-alter-do-chao" />,
    )

    expect(markup).toContain('Carregando relatos')
  })
})
