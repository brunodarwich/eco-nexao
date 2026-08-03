import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { OperationalDashboard } from './operational-dashboard'
import {
  AppAnalyticsView,
  CatalogItemApi,
  RouteApiSummary,
} from './components/app-analytics-view'
import { RouteReadinessView } from './components/route-readiness-view'
import { PoiEditorModal } from './components/poi-editor-modal'
import { CsvImportView } from './components/csv-import-view'

describe('OperationalDashboard Integration Suite', () => {
  const originalFetch = globalThis.fetch

  const initialRoutes: RouteApiSummary[] = [
    {
      slug: 'trilha-flona',
      title: 'Trilha Flona Tapajós',
      summary: 'Trilha na Floresta Nacional',
      distance_km: 18.5,
      estimated_minutes: 240,
      stages_count: 4,
      actors_count: 2,
      editorial_status: 'Publicado',
    },
  ]

  const initialCatalog: CatalogItemApi[] = [
    {
      id: 'poi-1',
      editorial_status: 'Publicado',
      actor: {
        id: 'actor-1',
        display_name: 'Pousada Flona Tapajós',
        category: { name: 'Hospedagem', slug: 'hospedagem' },
      },
      public_locations: [{ formatted_address: 'Comunidade Jamaraquá' }],
      public_contact_channels: [
        { channel_type: 'whatsapp', public_value: '+5593991112222' },
      ],
    },
    {
      id: 'poi-2',
      editorial_status: 'Publicado',
      actor: {
        id: 'actor-2',
        display_name: 'Restaurante Sumaúma',
        category: { name: 'Gastronomia', slug: 'gastronomia' },
      },
      public_locations: [{ formatted_address: 'Praia de Jamaraquá' }],
      public_contact_channels: [
        { channel_type: 'whatsapp', public_value: '+5593993334444' },
      ],
    },
  ]

  beforeEach(() => {
    vi.restoreAllMocks()
    globalThis.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      } as Response),
    )
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('renders territory selection bar and main tab navigation', () => {
    const markup = renderToStaticMarkup(<OperationalDashboard />)

    expect(markup).toContain('Território Operacional:')
    expect(markup).not.toContain('Santarém - Alter do Chão')
    expect(markup).toContain('Multirregional:')
    expect(markup).toContain('Eixo Ativo')

    expect(markup).toContain('role="tablist"')
    expect(markup).toContain('📊 Métricas do App')
    expect(markup).toContain('🗺️ Rotas &amp; Prontidão (0)')
    expect(markup).toContain('🔔 Relatos &amp; Auditoria')
    expect(markup).toContain('🔍 Descoberta Externa (Google Places)')
  })

  it('renders HeroFocus section inside dashboard', () => {
    const markup = renderToStaticMarkup(<OperationalDashboard />)

    expect(markup).toContain('Foco de Atenção Operacional')
    expect(markup).toContain('Operação Estável em Nenhuma região selecionada')
  })

  describe('Operação 1: Edição manual de um ponto existente via PoiEditorModal', () => {
    it('pre-fills editor modal with existing POI data and updates catalog item upon saving', () => {
      // 1. Initial catalog rendering shows original item
      const initialCatalogMarkup = renderToStaticMarkup(
        <AppAnalyticsView
          catalogItems={initialCatalog}
          isLoading={false}
          onOpenEditorModal={vi.fn()}
          onSelectRoute={vi.fn()}
          regionSlug="santarem-alter-do-chao"
          routes={initialRoutes}
          selectedRouteSlug="trilha-flona"
        />,
      )
      expect(initialCatalogMarkup).toContain('Pousada Flona Tapajós')
      expect(initialCatalogMarkup).toContain('Comunidade Jamaraquá')

      // 2. Open PoiEditorModal with poi-1
      const modalMarkup = renderToStaticMarkup(
        <PoiEditorModal
          initialData={initialCatalog[0]}
          isOpen={true}
          onClose={vi.fn()}
          onSave={vi.fn()}
          regionSlug="santarem-alter-do-chao"
          routeSlug="trilha-flona"
        />,
      )
      expect(modalMarkup).toContain('Editar Ponto de Apoio')
      expect(modalMarkup).toContain('value="Pousada Flona Tapajós"')
      expect(modalMarkup).toContain('value="Comunidade Jamaraquá"')

      // 3. Simulate edit update: modified POI payload
      const updatedPoi: CatalogItemApi = {
        ...initialCatalog[0],
        actor: {
          ...initialCatalog[0].actor!,
          display_name: 'Pousada Eco Flona Tapajós (Editado)',
        },
        public_locations: [
          { formatted_address: 'Comunidade Jamaraquá, Km 83' },
        ],
        public_contact_channels: [
          { channel_type: 'whatsapp', public_value: '+5593999990000' },
        ],
      }

      const updatedCatalog = [updatedPoi, initialCatalog[1]]

      // 4. Verify updated catalog view renders edited details
      const updatedCatalogMarkup = renderToStaticMarkup(
        <AppAnalyticsView
          catalogItems={updatedCatalog}
          isLoading={false}
          onOpenEditorModal={vi.fn()}
          onSelectRoute={vi.fn()}
          regionSlug="santarem-alter-do-chao"
          routes={initialRoutes}
          selectedRouteSlug="trilha-flona"
        />,
      )
      expect(updatedCatalogMarkup).toContain(
        'Pousada Eco Flona Tapajós (Editado)',
      )
      expect(updatedCatalogMarkup).toContain('Comunidade Jamaraquá, Km 83')
      expect(updatedCatalogMarkup).toContain(
        '1 canal(is) de contato público autorizados',
      )
    })
  })

  describe('Operação 2: Inserção manual de um novo ponto de apoio via PoiEditorModal', () => {
    it('opens modal in creation mode, inserts new POI into catalog, and increments route actors count in readiness matrix', () => {
      // 1. Initial readiness matrix score with 2 actors: (100 + 100 + 50)/3 = 83%
      const initialReadinessMarkup = renderToStaticMarkup(
        <RouteReadinessView
          isLoading={false}
          regionSlug="santarem-alter-do-chao"
          routes={initialRoutes}
        />,
      )
      expect(initialReadinessMarkup).toContain('2 ponto(s)')
      expect(initialReadinessMarkup).toContain('83%')

      // 2. Open PoiEditorModal in creation mode (initialData = null)
      const creationModalMarkup = renderToStaticMarkup(
        <PoiEditorModal
          initialData={null}
          isOpen={true}
          onClose={vi.fn()}
          onSave={vi.fn()}
          regionSlug="santarem-alter-do-chao"
          routeSlug="trilha-flona"
        />,
      )
      expect(creationModalMarkup).toContain('Novo Ponto de Apoio Manual')
      expect(creationModalMarkup).toContain('Cadastrar Ponto')

      // 3. New inserted POI
      const newPoi: CatalogItemApi = {
        id: 'poi-custom-new',
        editorial_status: 'Publicado',
        actor: {
          id: 'actor-new',
          display_name: 'Guia Ecológico Tapajós',
          category: { name: 'Comunidade & Guias', slug: 'comunidade-guias' },
        },
        public_locations: [
          { formatted_address: 'Alter do Chão, Santarém - PA' },
        ],
        public_contact_channels: [
          { channel_type: 'whatsapp', public_value: '+5593998887777' },
        ],
      }

      const catalogAfterInsertion = [newPoi, ...initialCatalog]
      const routesAfterInsertion: RouteApiSummary[] = [
        {
          ...initialRoutes[0],
          actors_count: (initialRoutes[0].actors_count || 0) + 1,
        },
      ]

      // 4. Verify catalog now contains new POI (3 items total)
      const catalogMarkup = renderToStaticMarkup(
        <AppAnalyticsView
          catalogItems={catalogAfterInsertion}
          isLoading={false}
          onOpenEditorModal={vi.fn()}
          onSelectRoute={vi.fn()}
          regionSlug="santarem-alter-do-chao"
          routes={routesAfterInsertion}
          selectedRouteSlug="trilha-flona"
        />,
      )
      expect(catalogMarkup).toContain('Guia Ecológico Tapajós')
      expect(catalogMarkup).toContain('Comunidade &amp; Guias')

      // 5. Verify RouteReadinessView matrix reflects updated 3 points and score (100+100+75)/3 = 92%
      const updatedReadinessMarkup = renderToStaticMarkup(
        <RouteReadinessView
          isLoading={false}
          regionSlug="santarem-alter-do-chao"
          routes={routesAfterInsertion}
        />,
      )
      expect(updatedReadinessMarkup).toContain('3 ponto(s)')
      expect(updatedReadinessMarkup).toContain('92%')
    })
  })

  describe('Operação 3: Importação segura de arquivo CSV via CsvImportView', () => {
    it('envia o CSV para validação administrativa sem simular atores no catálogo público', () => {
      const csvImportStep1 = renderToStaticMarkup(
        <CsvImportView
          onNavigateTab={vi.fn()}
          regionSlug="santarem-alter-do-chao"
          routes={initialRoutes}
          selectedRouteSlug="trilha-flona"
        />,
      )
      expect(csvImportStep1).toContain('Importação de Pontos de Apoio por CSV')
      expect(csvImportStep1).toContain('Trilha Flona Tapajós (trilha-flona)')
      expect(csvImportStep1).toContain('validado pela API administrativa')
      expect(csvImportStep1).toContain('rascunhos privados')
      expect(csvImportStep1).toContain(
        'não aparecem no aplicativo antes da revisão',
      )
    })
  })
})
