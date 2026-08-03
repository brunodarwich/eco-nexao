import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { PoiEditorModal } from './poi-editor-modal'
import { CatalogItemApi } from './app-analytics-view'

describe('PoiEditorModal Component', () => {
  const mockInitialPoi: CatalogItemApi = {
    id: 'poi-123',
    actor: {
      id: 'actor-123',
      display_name: 'Pousada Ventos do Tapajós',
      category: {
        name: 'Hospedagem',
        slug: 'hospedagem',
      },
    },
    public_locations: [
      {
        formatted_address: 'Av. Copacabana, 450, Alter do Chão',
        locality: 'Alter do Chão',
      },
    ],
    public_contact_channels: [
      {
        channel_type: 'whatsapp',
        public_value: '+5593998765432',
      },
    ],
  }

  it('renders nothing when isOpen is false', () => {
    const markup = renderToStaticMarkup(
      <PoiEditorModal
        initialData={null}
        isOpen={false}
        onClose={vi.fn()}
        onSave={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routeSlug="trilha-flona"
      />,
    )

    expect(markup).toBe('')
  })

  it('renders creation mode when isOpen is true and initialData is null', () => {
    const markup = renderToStaticMarkup(
      <PoiEditorModal
        initialData={null}
        isOpen={true}
        onClose={vi.fn()}
        onSave={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routeSlug="trilha-flona"
      />,
    )

    expect(markup).toContain('role="dialog"')
    expect(markup).toContain('Novo Ponto de Apoio Manual')
    expect(markup).toContain('Edição Direta no Painel')
    expect(markup).toContain('trilha-flona')
    expect(markup).toContain('Cadastrar Ponto')
    expect(markup).toContain('Cancelar')
    expect(markup).toContain('aria-label="Fechar modal"')
    expect(markup).toContain('aria-modal="true"')
    expect(markup).toContain('tabindex="-1"')
    expect(markup).toContain('data-autofocus')
  })

  it('renders edit mode with pre-filled initialData fields', () => {
    const markup = renderToStaticMarkup(
      <PoiEditorModal
        initialData={mockInitialPoi}
        isOpen={true}
        onClose={vi.fn()}
        onSave={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routeSlug="trilha-flona"
      />,
    )

    expect(markup).toContain('Editar Ponto de Apoio')
    expect(markup).toContain('value="Pousada Ventos do Tapajós"')
    expect(markup).toContain('value="Av. Copacabana, 450, Alter do Chão"')
    expect(markup).toContain('value="+5593998765432"')
    expect(markup).toContain('Salvar Alterações')
  })

  it('renders all category options in select element', () => {
    const markup = renderToStaticMarkup(
      <PoiEditorModal
        initialData={null}
        isOpen={true}
        onClose={vi.fn()}
        onSave={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routeSlug="trilha-flona"
      />,
    )

    expect(markup).toContain('Gastronomia')
    expect(markup).toContain('Hospedagem')
    expect(markup).toContain('Apoio Técnico')
    expect(markup).toContain('Artesanato &amp; Cultura')
    expect(markup).toContain('Comunidade &amp; Guias')
    expect(markup).toContain('Emergência &amp; Saúde')
  })

  it('renders editorial status options in select element', () => {
    const markup = renderToStaticMarkup(
      <PoiEditorModal
        initialData={null}
        isOpen={true}
        onClose={vi.fn()}
        onSave={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routeSlug="trilha-flona"
      />,
    )

    expect(markup).toContain('Rascunho (Não publicado)')
    expect(markup).toContain('Em Revisão Editorial')
    expect(markup).toContain('Publicado no App')
  })

  it('renders edit mode with pre-filled fields and save changes button (Operation 1)', () => {
    const markup = renderToStaticMarkup(
      <PoiEditorModal
        initialData={mockInitialPoi}
        isOpen={true}
        onClose={vi.fn()}
        onSave={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routeSlug="trilha-flona"
      />,
    )

    expect(markup).toContain('Editar Ponto de Apoio')
    expect(markup).toContain('value="Pousada Ventos do Tapajós"')
    expect(markup).toContain('value="Av. Copacabana, 450, Alter do Chão"')
    expect(markup).toContain('value="+5593998765432"')
    expect(markup).toContain('Salvar Alterações')
  })

  it('renders creation mode with initial fields for new support point insertion (Operation 2)', () => {
    const markup = renderToStaticMarkup(
      <PoiEditorModal
        initialData={null}
        isOpen={true}
        onClose={vi.fn()}
        onSave={vi.fn()}
        regionSlug="santarem-alter-do-chao"
        routeSlug="trilha-flona"
      />,
    )

    expect(markup).toContain('Novo Ponto de Apoio Manual')
    expect(markup).toContain('Cadastrar Ponto')
    expect(markup).toContain('Gastronomia')
    expect(markup).toContain('Rascunho (Não publicado)')
  })
})
