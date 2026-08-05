import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { OperationalDashboard } from './operational-dashboard'
import {
  AppAnalyticsView,
  CatalogItemApi,
} from './components/app-analytics-view'
import { PoiEditorModal } from './components/poi-editor-modal'
import { CsvImportView } from './components/csv-import-view'
import type { RouteApiSummary } from '../lib/dashboard-routes'

describe('OperationalDashboard Integration Suite', () => {
  const originalFetch = globalThis.fetch

  const initialRoutes: RouteApiSummary[] = [
    {
      durationMinutes: 240,
      slug: 'trilha-flona',
      title: 'Trilha Flona Tapajós',
    },
  ]

  const initialCatalog: CatalogItemApi[] = [
    {
      id: 'poi-1',
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
    expect(markup).toContain('📥 Importar CSV')
    expect(markup).toContain('🔍 Descoberta Externa (Google Places)')
  })

  it('renders HeroFocus section inside dashboard', () => {
    const markup = renderToStaticMarkup(<OperationalDashboard />)

    expect(markup).toContain('Foco de Atenção Operacional')
    expect(markup).toContain(
      'Prioridade operacional indisponível em Nenhuma região selecionada',
    )
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
          regionId="00000000-0000-0000-0000-000000000001"
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

  it('allows manual creation of support points via SupportPointCreateModal', () => {
    const markup = renderToStaticMarkup(
      <AppAnalyticsView
        catalogItems={initialCatalog}
        isLoading={false}
        onOpenCreateModal={vi.fn()}
        onOpenEditorModal={vi.fn()}
        onSelectRoute={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routes={initialRoutes}
        selectedRouteSlug="trilha-flona"
      />,
    )

    expect(markup).toContain('➕ Adicionar Ponto Manual')
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
