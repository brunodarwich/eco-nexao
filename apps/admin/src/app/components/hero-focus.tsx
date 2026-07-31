'use client'

import { Button } from '@econexao/ui/button'

interface HeroFocusProps {
  regionName: string
  routeCount: number
  activeRouteName: string
  alertsCount: number
  pendingRevisionsCount: number
  onNavigateTab: (tab: 'analytics' | 'routes' | 'reports' | 'discovery') => void
}

export function HeroFocus({
  regionName,
  routeCount,
  activeRouteName,
  alertsCount,
  pendingRevisionsCount,
  onNavigateTab,
}: HeroFocusProps) {
  const hasAlerts = alertsCount > 0
  const hasRevisions = pendingRevisionsCount > 0

  return (
    <section aria-labelledby="hero-focus-title" className="hero-focus-card">
      <div className="hero-focus-badge">
        <span className="hero-focus-dot" />
        Foco de Atenção Operacional
      </div>

      <div className="hero-focus-content">
        <h2 id="hero-focus-title">
          {hasAlerts
            ? `Atenção: ${alertsCount} alerta(s) de segurança ativo(s) em ${regionName}`
            : hasRevisions
              ? `${pendingRevisionsCount} revisão(ões) editorial(is) aguardando aprovação`
              : `Operação Estável em ${regionName}`}
        </h2>

        <p className="hero-focus-description">
          {hasAlerts
            ? `Existem alertas comunitários ou climáticos ativos que impactam o acesso às rotas da região ${regionName}. Verifique a triagem.`
            : hasRevisions
              ? `Há alterações de conteúdo aguardando validação editorial antes de serem publicadas no aplicativo.`
              : routeCount > 0
                ? `Todas as ${routeCount} rota(s) cadastradas em ${regionName} estão com status regular. A rota atual de referência é "${activeRouteName}".`
                : `Nenhuma rota ativa encontrada em ${regionName}. Cadastre ou importe rotas para ativar o monitoramento.`}
        </p>

        <div className="hero-focus-actions">
          {hasAlerts ? (
            <Button onClick={() => onNavigateTab('reports')} type="button">
              🚨 Triar Alertas ({alertsCount})
            </Button>
          ) : hasRevisions ? (
            <Button onClick={() => onNavigateTab('routes')} type="button">
              📝 Ver Revisões ({pendingRevisionsCount})
            </Button>
          ) : (
            <Button onClick={() => onNavigateTab('analytics')} type="button">
              📊 Ver Desempenho do App
            </Button>
          )}

          <Button
            onClick={() => onNavigateTab('routes')}
            type="button"
            variant="secondary"
          >
            🗺️ Matriz de Prontidão ({routeCount} rotas)
          </Button>
        </div>
      </div>
    </section>
  )
}
