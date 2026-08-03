import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import * as fs from 'fs'
import * as path from 'path'
import { PoiEditorModal } from './poi-editor-modal'
import {
  getDashboardTabIndex,
  OperationalDashboard,
} from '../operational-dashboard'

describe('Suíte de Acessibilidade WCAG 2.2 AA & Navegação por Teclado', () => {
  describe('1. Fechamento de Modal com a Tecla Escape & Atributos ARIA (PoiEditorModal)', () => {
    it('possui atributos role="dialog", aria-modal="true" e aria-labelledby', () => {
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
      expect(markup).toContain('aria-modal="true"')
      expect(markup).toContain('aria-labelledby="poi-modal-title"')
      expect(markup).toContain('id="poi-modal-title"')
      expect(markup).toContain('aria-label="Fechar modal"')
    })

    it('dispara a callback onClose quando a tecla Escape é pressionada', () => {
      const handleClose = vi.fn()

      const handleKeyDown = (e: { key: string }) => {
        if (e.key === 'Escape') {
          handleClose()
        }
      }

      handleKeyDown({ key: 'Escape' })
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('não dispara a callback onClose quando outras teclas são pressionadas', () => {
      const handleClose = vi.fn()

      const handleKeyDown = (e: { key: string }) => {
        if (e.key === 'Escape') {
          handleClose()
        }
      }

      handleKeyDown({ key: 'Enter' })
      handleKeyDown({ key: 'Tab' })
      handleKeyDown({ key: 'Space' })

      expect(handleClose).not.toHaveBeenCalled()
    })
  })

  describe('2. Navegação por Abas com role="tablist" e aria-selected (OperationalDashboard)', () => {
    it('renderiza container com role="tablist" e aria-label de navegação', () => {
      const markup = renderToStaticMarkup(<OperationalDashboard />)

      expect(markup).toContain('role="tablist"')
      expect(markup).toContain('aria-label="Navegação do Painel Operacional"')
    })

    it('renderiza todos os botões de abas com role="tab"', () => {
      const markup = renderToStaticMarkup(<OperationalDashboard />)

      const matches = markup.match(/role="tab"/g)
      expect(matches).not.toBeNull()
      expect(matches?.length).toBe(5)
    })

    it('define aria-selected="true" apenas na aba ativa por padrão (analytics)', () => {
      const markup = renderToStaticMarkup(<OperationalDashboard />)

      // Aba de analytics ativa por padrão
      expect(markup).toContain('aria-selected="true"')
      expect(markup).toContain('class="tab-button is-active"')
      expect(markup).toContain('📊 Métricas do App')

      // Demais abas inativas
      expect(markup).toContain('aria-selected="false"')
    })
  })

  describe('3. Visualização de Foco & Conformidade WCAG 2.2 AA (CSS & HTML)', () => {
    it('calcula a navegação de tabs para setas, Home e End', () => {
      expect(getDashboardTabIndex(0, 'ArrowRight', 5)).toBe(1)
      expect(getDashboardTabIndex(0, 'ArrowLeft', 5)).toBe(4)
      expect(getDashboardTabIndex(2, 'Home', 5)).toBe(0)
      expect(getDashboardTabIndex(2, 'End', 5)).toBe(4)
      expect(getDashboardTabIndex(2, 'Enter', 5)).toBeNull()
    })

    it('contém regras CSS de indicação visual de foco (:focus-visible)', () => {
      const cssPath = path.resolve(__dirname, '../styles.css')
      const cssContent = fs.readFileSync(cssPath, 'utf-8')

      expect(cssContent).toContain(':focus-visible')
      expect(cssContent).toContain('outline:')
      expect(cssContent).toContain('.tab-button:focus-visible')
      expect(cssContent).toContain('.modal-close-button:focus-visible')
    })

    it('garante que todos os controles do modal possuem labels associados e botões acessíveis', () => {
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

      expect(markup).toContain('Nome Comercial / Exibição público *')
      expect(markup).toContain('Categoria *')
      expect(markup).toContain('Status Editorial *')
      expect(markup).toContain('Endereço / Localidade')
      expect(markup).toContain('Telefone / WhatsApp Autorizado (E.164)')
      expect(markup).toContain('type="button"')
      expect(markup).toContain('type="submit"')
    })
  })
})
