import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import {
  AppAnalyticsView,
  CatalogItemApi,
  RouteApiSummary,
} from './app-analytics-view'

describe('AppAnalyticsView Component', () => {
  const mockRoutes: RouteApiSummary[] = [
    {
      actors_count: 5,
      distance_km: 18.5,
      editorial_status: 'Publicado',
      estimated_minutes: 240,
      slug: 'trilha-flona',
      stages_count: 4,
      summary: 'Trilha principal na Floresta Nacional',
      title: 'Trilha Flona Tapajós',
    },
    {
      actors_count: 2,
      distance_km: 8.0,
      editorial_status: 'Em Revisão',
      estimated_minutes: 120,
      slug: 'travessia-alter',
      stages_count: 2,
      summary: 'Travessia de barco e caminhada em Alter do Chão',
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

    expect(markup).toContain('Rotas Ativas')
    expect(markup).toContain('2')
    expect(markup).toContain('Estágios Mapeados')
    expect(markup).toContain('6')
    expect(markup).toContain('Pontos de Apoio')

    expect(markup).toContain('Trilha Flona Tapajós')
    expect(markup).toContain('18.5 km')
    expect(markup).toContain('4 estágio(s)')

    expect(markup).toContain('Travessia Alter do Chão')
    expect(markup).toContain('8 km')
  })

  it('renders POI details and readiness completeness score in catalog list', () => {
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
})
