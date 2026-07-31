import { describe, expect, it } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { RouteReadinessView } from './route-readiness-view'
import { RouteApiSummary } from './app-analytics-view'

describe('RouteReadinessView Component', () => {
  const mockRoutes: RouteApiSummary[] = [
    {
      actors_count: 4,
      distance_km: 12.0,
      editorial_status: 'Publicado',
      estimated_minutes: 180,
      slug: 'trilha-flona',
      stages_count: 3,
      summary: 'Resumo da trilha',
      title: 'Trilha Flona Tapajós',
    },
    {
      actors_count: 0,
      distance_km: 0,
      editorial_status: 'Rascunho',
      estimated_minutes: 0,
      slug: 'trilha-nova',
      stages_count: 0,
      summary: '',
      title: 'Trilha Nova',
    },
  ]

  it('renders loading state when isLoading is true', () => {
    const markup = renderToStaticMarkup(
      <RouteReadinessView
        isLoading={true}
        regionSlug="santarem-alter-do-chao"
        routes={[]}
      />,
    )

    expect(markup).toContain('Carregando matriz de prontidão')
    expect(markup).toContain(
      'Consultando a matriz de prontidão das rotas em...',
    )
  })

  it('renders empty feedback state when routes array is empty', () => {
    const markup = renderToStaticMarkup(
      <RouteReadinessView
        isLoading={false}
        regionSlug="santarem-alter-do-chao"
        routes={[]}
      />,
    )

    expect(markup).toContain('Matriz sem dados')
    expect(markup).toContain('Nenhuma rota encontrada para a região')
    expect(markup).toContain('santarem-alter-do-chao')
  })

  it('renders readiness matrix table with calculated readiness scores', () => {
    const markup = renderToStaticMarkup(
      <RouteReadinessView
        isLoading={false}
        regionSlug="santarem-alter-do-chao"
        routes={mockRoutes}
      />,
    )

    expect(markup).toContain('Matriz de Prontidão e Estado Editorial')
    expect(markup).toContain('Trilha Flona Tapajós')
    expect(markup).toContain('trilha-flona')
    expect(markup).toContain('status--published')
    expect(markup).toContain('Publicado')
    expect(markup).toContain('3 estágio(s) • 12 km')
    expect(markup).toContain('4 ponto(s)')

    expect(markup).toContain('Trilha Nova')
    expect(markup).toContain('trilha-nova')
    expect(markup).toContain('status--draft')
    expect(markup).toContain('Rascunho')
  })
})
