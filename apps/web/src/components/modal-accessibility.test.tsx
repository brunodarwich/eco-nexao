import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { ReportIssueModal } from './report-issue-modal'

describe('diálogos públicos acessíveis', () => {
  it('expõe nome, modalidade e foco inicial no relato', () => {
    const markup = renderToStaticMarkup(
      <ReportIssueModal
        isOpen
        onClose={vi.fn()}
        targetType="route"
        targetName="Rota de teste"
      />,
    )

    expect(markup).toContain('role="dialog"')
    expect(markup).toContain('aria-modal="true"')
    expect(markup).toContain('aria-labelledby="report-modal-title"')
    expect(markup).toContain('tabindex="-1"')
    expect(markup).toContain('data-autofocus')
  })
})
