import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'
import { CatalogItemApi } from './app-analytics-view'
import { PoiEditorModal } from './poi-editor-modal'

describe('PoiEditorModal', () => {
  const initialPoi: CatalogItemApi = {
    actor: {
      id: '00000000-0000-0000-0000-000000000002',
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

  function render(initialData: CatalogItemApi | null = initialPoi) {
    return renderToStaticMarkup(
      <PoiEditorModal
        initialData={initialData}
        isOpen
        onClose={vi.fn()}
        onSave={vi.fn()}
        regionId="00000000-0000-0000-0000-000000000001"
        routeSlug="trilha-flona"
      />,
    )
  }

  it('renders nothing when closed or when no existing actor was selected', () => {
    const closed = renderToStaticMarkup(
      <PoiEditorModal
        initialData={initialPoi}
        isOpen={false}
        onClose={vi.fn()}
        onSave={vi.fn()}
        regionId="00000000-0000-0000-0000-000000000001"
        routeSlug="trilha-flona"
      />,
    )

    expect(closed).toBe('')
    expect(render(null)).toBe('')
  })

  it('renders an accessible editor with the existing actor data', () => {
    const markup = render()

    expect(markup).toContain('role="dialog"')
    expect(markup).toContain('aria-modal="true"')
    expect(markup).toContain('aria-labelledby="poi-modal-title"')
    expect(markup).toContain('data-autofocus')
    expect(markup).toContain('Editar Ponto de Apoio')
    expect(markup).toContain('value="Pousada Ventos do Tapajós"')
    expect(markup).toContain('value="Av. Copacabana, 450, Alter do Chão"')
    expect(markup).toContain('value="+5593998765432"')
  })

  it('makes the draft-only workflow explicit', () => {
    const markup = render()

    expect(markup).toContain('Salvar alterações como rascunho')
    expect(markup).toContain(
      'A pré-visualização só é atualizada depois que a API confirma o rascunho.',
    )
    expect(markup).toContain(
      'Revisão e publicação usam ações próprias do workflow.',
    )
    expect(markup).not.toContain('Publicado no App')
    expect(markup).not.toContain('Cadastrar Ponto')
  })

  it('renders the supported category options', () => {
    const markup = render()

    expect(markup).toContain('Gastronomia')
    expect(markup).toContain('Hospedagem')
    expect(markup).toContain('Apoio Técnico')
    expect(markup).toContain('Artesanato &amp; Cultura')
    expect(markup).toContain('Comunidade &amp; Guias')
    expect(markup).toContain('Emergência &amp; Saúde')
  })
})
