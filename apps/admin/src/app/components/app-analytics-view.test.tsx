import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { AppAnalyticsView, CatalogItemApi } from './app-analytics-view'
import type { RouteApiSummary } from '../../lib/dashboard-routes'

describe('AppAnalyticsView Component', () => {
  const mockRoutes: RouteApiSummary[] = [
    {
      durationMinutes: 240,
      slug: 'trilha-flona',
      title: 'Trilha Flona Tapajós',
    },
    {
      durationMinutes: 120,
      slug: 'travessia-alter',
      title: 'Travessia Alter do Chão',
    },
  ]

  const mockCatalogItems: CatalogItemApi[] = [
    {
      actor: {
        category: { name: 'Alimentação & Restauração', slug: 'alimentacao' },
        display_name: 'Restaurante Doce de Caju',
        id: 'actor-1',
      },
      id: 'cat-1',
      public_contact_channels: [
        { channel_type: 'whatsapp', public_value: '+559399999999' },
      ],
      public_locations: [
        { formatted_address: 'Rua Principal, 100, Alter do Chão' },
      ],
    },
  ]

  it('renders loading state when isLoading is true', () => {
    const markup = renderToStaticMarkup(
      <AppAnalyticsView
        catalogItems={[]}
        isLoading={true}
        onOpenEditorModal={vi.fn()}
        onSelectRoute={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routes={[]}
        selectedRouteSlug=""
      />,
    )

    expect(markup).toContain('Carregando dados do aplicativo')
    expect(markup).toContain('Buscando informações da região')
  })

  it('renders empty routes feedback state when routes array is empty', () => {
    const markup = renderToStaticMarkup(
      <AppAnalyticsView
        catalogItems={[]}
        isLoading={false}
        onOpenEditorModal={vi.fn()}
        onSelectRoute={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routes={[]}
        selectedRouteSlug=""
      />,
    )

    expect(markup).toContain('Nenhuma rota disponível')
    expect(markup).toContain(
      'Não foram encontradas rotas publicadas para a região',
    )
    expect(markup).toContain('santarem-alter-do-chao')
  })

  it('renders KPI metrics and route selection list when routes exist', () => {
    const markup = renderToStaticMarkup(
      <AppAnalyticsView
        catalogItems={mockCatalogItems}
        isLoading={false}
        onOpenEditorModal={vi.fn()}
        onSelectRoute={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routes={mockRoutes}
        selectedRouteSlug="trilha-flona"
      />,
    )

    expect(markup).toContain('Rotas Publicadas')
    expect(markup).toContain('2')
    expect(markup).toContain('Duração da Rota')
    expect(markup).toContain('240')
    expect(markup).toContain('Pontos de Apoio')

    expect(markup).toContain('Trilha Flona Tapajós')
    expect(markup).toContain('240 minutos estimados')

    expect(markup).toContain('Travessia Alter do Chão')
    expect(markup).toContain('120 minutos estimados')
    expect(markup).toContain('métricas consentidas')
    expect(markup).toContain('Dados indisponíveis ou suprimidos')
  })

  it('renders POI details and public-data completeness in catalog list', () => {
    const markup = renderToStaticMarkup(
      <AppAnalyticsView
        catalogItems={mockCatalogItems}
        isLoading={false}
        onOpenEditorModal={vi.fn()}
        onSelectRoute={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routes={mockRoutes}
        selectedRouteSlug="trilha-flona"
      />,
    )

    expect(markup).toContain('Restaurante Doce de Caju')
    expect(markup).toContain('Alimentação &amp; Restauração')
    expect(markup).toContain('Rua Principal, 100, Alter do Chão')
    expect(markup).toContain('1 canal(is) de contato público autorizados')
    expect(markup).toContain('Dados públicos disponíveis')
    expect(markup).toContain('100%')
  })

  it('renders empty state when selected route has no catalog items', () => {
    const markup = renderToStaticMarkup(
      <AppAnalyticsView
        catalogItems={[]}
        isLoading={false}
        onOpenEditorModal={vi.fn()}
        onSelectRoute={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routes={mockRoutes}
        selectedRouteSlug="travessia-alter"
      />,
    )

    expect(markup).toContain('Nenhum ponto vinculado')
    expect(markup).toContain(
      'Não há pontos de apoio cadastrados no catálogo para a rota',
    )
    expect(markup).toContain('Travessia Alter do Chão')
  })

  it('renders aggregates and ranking only from the administrative contract', () => {
    const markup = renderToStaticMarkup(
      <AppAnalyticsView
        catalogItems={mockCatalogItems}
        isLoading={false}
        onOpenEditorModal={vi.fn()}
        onSelectRoute={vi.fn()}
        operationalData={{
          region_slug: 'santarem-alter-do-chao',
          route_slug: 'trilha-flona',
          start: '2026-07-07',
          end: '2026-08-05',
          privacy_threshold: 10,
          metrics: [
            { event_name: 'contact_opened', count: 14, suppressed: false },
            { event_name: 'route_opened', count: null, suppressed: true },
          ],
          ranking: [
            {
              support_point_id: '00000000-0000-4000-8000-000000000001',
              support_point_name: 'Restaurante Doce de Caju',
              contacts: 14,
            },
          ],
        }}
        regionSlug="santarem-alter-do-chao"
        routes={mockRoutes}
        selectedRouteSlug="trilha-flona"
      />,
    )

    expect(markup).toContain('14 contatos')
    expect(markup).toContain('indisponível ou suprimido')
  })
})
