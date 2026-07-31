import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { HeroFocus } from './hero-focus'

describe('HeroFocus Component', () => {
  it('renders stable operation state when no alerts and no pending revisions', () => {
    const handleNavigate = vi.fn()
    const markup = renderToStaticMarkup(
      <HeroFocus
        activeRouteName="Trilha da Flona"
        alertsCount={0}
        onNavigateTab={handleNavigate}
        pendingRevisionsCount={0}
        regionName="Santarém - Alter do Chão"
        routeCount={3}
      />,
    )

    expect(markup).toContain('Foco de Atenção Operacional')
    expect(markup).toContain('Operação Estável em Santarém - Alter do Chão')
    expect(markup).toContain(
      'Todas as 3 rota(s) cadastradas em Santarém - Alter do Chão estão com status regular',
    )
    expect(markup).toContain('Trilha da Flona')
    expect(markup).toContain('📊 Ver Desempenho do App')
    expect(markup).toContain('🗺️ Matriz de Prontidão (3 rotas)')
  })

  it('renders alert focus state when alerts are active', () => {
    const handleNavigate = vi.fn()
    const markup = renderToStaticMarkup(
      <HeroFocus
        activeRouteName="Trilha da Flona"
        alertsCount={2}
        onNavigateTab={handleNavigate}
        pendingRevisionsCount={0}
        regionName="Santarém - Alter do Chão"
        routeCount={3}
      />,
    )

    expect(markup).toContain(
      'Atenção: 2 alerta(s) de segurança ativo(s) em Santarém - Alter do Chão',
    )
    expect(markup).toContain('impactam o acesso às rotas da região')
    expect(markup).toContain('🚨 Triar Alertas (2)')
  })

  it('renders revision focus state when pending revisions exist without alerts', () => {
    const handleNavigate = vi.fn()
    const markup = renderToStaticMarkup(
      <HeroFocus
        activeRouteName="Trilha da Flona"
        alertsCount={0}
        onNavigateTab={handleNavigate}
        pendingRevisionsCount={5}
        regionName="Santarém - Alter do Chão"
        routeCount={3}
      />,
    )

    expect(markup).toContain(
      '5 revisão(ões) editorial(is) aguardando aprovação',
    )
    expect(markup).toContain('aguardando validação editorial')
    expect(markup).toContain('📝 Ver Revisões (5)')
  })

  it('renders empty routes notice when route count is zero', () => {
    const handleNavigate = vi.fn()
    const markup = renderToStaticMarkup(
      <HeroFocus
        activeRouteName="Nenhuma"
        alertsCount={0}
        onNavigateTab={handleNavigate}
        pendingRevisionsCount={0}
        regionName="Santarém - Alter do Chão"
        routeCount={0}
      />,
    )

    expect(markup).toContain(
      'Nenhuma rota ativa encontrada em Santarém - Alter do Chão',
    )
  })
})
