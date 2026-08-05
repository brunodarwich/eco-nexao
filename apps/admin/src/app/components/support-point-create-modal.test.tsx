import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'
import { SupportPointCreateModal } from './support-point-create-modal'

describe('SupportPointCreateModal', () => {
  const routes = [
    {
      id: 'e706d05c-9f73-4543-9d6d-dbb93d60d87e',
      title: 'Rota Pindobal',
      slug: 'rota-pindobal',
      durationMinutes: 60,
    },
  ]

  function render(isOpen = true) {
    return renderToStaticMarkup(
      <SupportPointCreateModal
        isOpen={isOpen}
        onClose={vi.fn()}
        onSave={vi.fn()}
        regionId="00000000-0000-0000-0000-000000000001"
        regionSlug="alter-do-chao"
        routes={routes}
        selectedRouteSlug="rota-pindobal"
      />,
    )
  }

  it('renders nothing when closed', () => {
    const markup = render(false)
    expect(markup).toBe('')
  })

  it('renders an accessible multi-step wizard dialog when open', () => {
    const markup = render(true)

    expect(markup).toContain('role="dialog"')
    expect(markup).toContain('aria-modal="true"')
    expect(markup).toContain('aria-labelledby="support-point-modal-title"')
    expect(markup).toContain('Novo Ponto de Apoio')
    expect(markup).toContain('1. Dados Básicos')
    expect(markup).toContain('2. Localização')
    expect(markup).toContain('3. Contatos')
    expect(markup).toContain('4. Rota')
    expect(markup).toContain('5. Resumo')
  })

  it('explicitly states mandatory draft status and human editorial workflow', () => {
    const markup = render(true)

    expect(markup).toContain(
      'O cadastro cria um agregado completo obrigatoriamente em estado',
    )
    expect(markup).toContain('Rascunho')
    expect(markup).not.toContain('Publicar direto')
  })
})
