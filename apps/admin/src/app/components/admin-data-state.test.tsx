import { describe, expect, it } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { AdminDataState, classifyAdminResponse } from './admin-data-state'

describe('admin data states', () => {
  it.each([
    [401, 'unauthorized', 'Sessão necessária'],
    [403, 'forbidden', 'Acesso não autorizado'],
    [429, 'rate-limited', 'Muitas tentativas'],
    [500, 'server-error', 'Falha no serviço'],
    [503, 'server-error', 'Falha no serviço'],
    [0, 'unavailable', 'Serviço indisponível'],
  ])('maps %s to the explicit admin state', (status, state, title) => {
    expect(classifyAdminResponse(status)).toBe(state)
    expect(renderToStaticMarkup(<AdminDataState error={state as never} />)).toContain(title)
  })

  it('offers recovery without replacing the error with an empty state', () => {
    const markup = renderToStaticMarkup(
      <AdminDataState error="server-error" onRetry={() => undefined} />,
    )
    expect(markup).toContain('Tentar novamente')
    expect(markup).toContain('Falha no serviço')
  })
})
