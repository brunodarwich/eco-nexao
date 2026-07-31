import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { CsvImportView } from './csv-import-view'
import { RouteApiSummary } from './app-analytics-view'

describe('CsvImportView Component', () => {
  const routes: RouteApiSummary[] = [
    {
      actors_count: 2,
      editorial_status: 'Em Revisão',
      slug: 'pindobal',
      stages_count: 3,
      title: 'Rota de Pindobal',
    },
  ]

  function render(selectedRouteSlug = 'pindobal', availableRoutes = routes) {
    return renderToStaticMarkup(
      <CsvImportView
        onNavigateTab={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routes={availableRoutes}
        selectedRouteSlug={selectedRouteSlug}
      />,
    )
  }

  it('explica que a API valida e grava somente rascunhos privados', () => {
    const markup = render()
    expect(markup).toContain('Importação de Pontos de Apoio por CSV')
    expect(markup).toContain('validado pela API administrativa')
    expect(markup).toContain('rascunhos privados')
    expect(markup).toContain('não aparecem no aplicativo antes da revisão')
  })

  it('mostra o fluxo de quatro etapas e o gabarito oficial', () => {
    const markup = render()
    expect(markup).toContain('1. Seleção &amp; Envio')
    expect(markup).toContain('2. Validação &amp; Prévia')
    expect(markup).toContain('3. Confirmar Rascunhos')
    expect(markup).toContain('4. Concluído')
    expect(markup).toContain('/schemas/catalogo-template.csv')
  })

  it('pré-seleciona a rota e informa que o servidor confere região e rota', () => {
    const markup = render()
    expect(markup).toContain('Rota de Pindobal (pindobal)')
    expect(markup).toContain('santarem-alter-do-chao')
    expect(markup).toContain('A API também confere a região e a rota')
  })

  it('mantém o envio disponível quando a lista de rotas está vazia', () => {
    const markup = render('', [])
    expect(markup).toContain('<select></select>')
    expect(markup).toContain('Arquivo CSV do catálogo *')
    expect(markup).toContain('Validar no servidor')
  })
})
