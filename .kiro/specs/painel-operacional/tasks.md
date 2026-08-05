# Tasks - Painel Operacional Administrativo (Reflexo do App)

- [x] 1. Criar estrutura de componentes e abas no painel operacional (`apps/admin`) _Requisitos: RF-ADM-01, RF-ADM-05_
  - Criar `operational-dashboard.tsx` com navegação por abas (`analytics`, `routes`, `reports`,
    `import`, `discovery`).
  - Atualizar `page.tsx` para renderizar a nova experiência operacional.
  - Arquivos: `apps/admin/src/app/operational-dashboard.tsx`, `apps/admin/src/app/page.tsx`

- [x] 2. Implementar Card Hero de Foco Recomendado (TDAH) _Requisitos: RF-ADM-01, RNF-ADM-01_
  - [x] 2.1 Criar `components/hero-focus.tsx` com composição e ações acessíveis.
  - [x] 2.2 Remover a declaração de estabilidade baseada em contadores fixos e apresentar estado
    parcial explícito.
  - [x] 2.3 Priorizar alertas e revisões reais.
  - Arquivos: `apps/admin/src/app/components/hero-focus.tsx`,
    `apps/admin/src/app/operational-dashboard.tsx`,
    `apps/admin/src/lib/admin-api.ts`,
    `services/api/modules/reports/views.py`,
    `services/api/modules/reports/serializers.py`,
    `services/api/modules/reports/urls.py`,
    `services/api/modules/reports/test_admin_dashboard_summary.py`,
    `services/api/config/tests/test_openapi_contracts.py`,
    `packages/contracts/openapi/schema.yaml`,
    `packages/contracts/src/api.ts`,
    `apps/admin/src/app/api/admin/[...path]/route.ts`.
  - Verificação: endpoint `GET /api/v1/admin/dashboard/summary` autenticado e regionalmente
    autorizado retorna `active_alerts_count`, `priority_reports_count` e `pending_revisions_count`.
    O Hero exibe "Prioridade operacional indisponível" enquanto carrega ou em erro, e declara
    estabilidade somente quando contadores reais forem zero. Backend: 284 passed, 1 skipped.
    Admin: 60 passed. Web: 27 passed. `pnpm check` aprovado em 2026-08-05.

- [x] 3. Implementar visão de Analytics do App e Cliques em Pontos de Apoio _Requisitos: RF-ADM-02_
  - [x] 3.1 Exibir o total real de eventos consentidos retornado pelo resumo administrativo.
  - [x] 3.2 Separar a consulta do catálogo publicado de métricas de engajamento e remover textos que
    apresentavam completude cadastral como acesso de usuários.
  - [x] 3.3 Exibir sessões, rotas abertas, contatos, downloads e ranking por ponto.
    - Especificação aprovada neste artefato: allowlist de quatro eventos, dimensão técnica de ponto
      apenas em `contact_opened`, retenção de bruto sem ID por 24h, agregado por 13 meses e
      supressão `<10`; ver `requirements.md` e `design.md`.
    - Arquivos: `services/api/modules/analytics/{models.py,serializers.py,views.py,throttles.py,test_analytics.py,migrations/0003_operational_analytics_privacy.py,management/commands/purge_analytics.py}`, `apps/web/src/{lib/analytics-sdk.ts,components/analytics-lifecycle.tsx,components/route-experience.tsx,components/route-local-actions.tsx}`, `apps/admin/src/app/components/app-analytics-view.tsx`, `packages/contracts/{openapi/schema.yaml,src/api.ts}`.
    - Verificação: allowlist mínima, consentimento/revogação, rejeição de PII/coordenadas, lote atômico, chave agregada não nula, retenção 24h/13 meses, escopo regional, limiar 10, ranking e resposta OpenAPI cobertos; `pnpm check` aprovado em 2026-08-05.

- [x] 4. Implementar Matriz de Prontidão de Rotas e Estado Editorial _Requisitos: RF-ADM-03_
  - [x] 4.1 Criar a apresentação da matriz e o estado explícito de dados indisponíveis.
  - [x] 4.2 Separar o DTO público do modelo administrativo e impedir scores derivados de campos
    ausentes.
  - [x] 4.3 Fornecer status e dimensões reais de prontidão por rota.
    - Fórmula, bloqueadores e contrato administrativo especificados em `requirements.md` e
      `design.md`; implementação verificada.
    - Arquivos: `services/api/modules/routes/{readiness.py,admin_serializers.py,views.py,urls.py,throttles.py,test_admin_readiness.py}`, `apps/admin/src/app/components/{route-readiness-view.tsx,route-readiness-view.test.tsx}`, `packages/contracts/{openapi/schema.yaml,src/api.ts}`.
    - Verificação: fórmula versionada 30/25/20/15/10, bloqueadores, estados editoriais, catálogo, contatos, alertas, revisão, versão, região vazia, autorização, throttle, OpenAPI real e matriz renderizada; `pnpm check` aprovado em 2026-08-05 com 284 testes backend aprovados (1 skipped), 64 testes admin e 27 testes web, além dos dois builds Next.js.

- [x] 5. Implementar Central de Triagem de Relatos e Alertas _Requisitos: RF-ADM-04_
  - Criar `components/reports-alerts-view.tsx` com fila de relatos da comunidade categorizados por prioridade.
  - Arquivo: `apps/admin/src/app/components/reports-alerts-view.tsx`

- [x] 6. Reorganizar estilos CSS e validar acessibilidade WCAG 2.2 AA _Requisitos: RNF-ADM-01_
  - Atualizar `styles.css` garantindo tema claro/escuro e navegação fluida por teclado.
  - Arquivo: `apps/admin/src/app/styles.css`

- [x] 7. Implementar aba de Importação CSV por Rota com prévia e validação _Requisitos: RF-ADM-06_
  - Criar `components/csv-import-view.tsx` com wizard de 4 passos, estatísticas de prévia e gravação em rascunho.
  - Arquivo: `apps/admin/src/app/components/csv-import-view.tsx`

- [x] 8. Implementar edição manual e cadastro de pontos com persistência real _Requisitos: RF-ADM-07_
  - [x] 8.1 Corrigir edição de ator existente para usar UUIDs reais, cliente administrativo
    compartilhado e sucesso confirmado pela API.
  - [x] 8.2 Remover fallback local e preservar o formulário em falhas HTTP ou de rede.
  - [x] 8.3 Implementar cadastro manual de ator novo com localização, contato e vínculo de rota.
  - Arquivos: `apps/admin/src/app/components/support-point-create-modal.tsx`,
    `apps/admin/src/app/components/support-point-create-modal.test.tsx`,
    `apps/admin/src/app/api/admin/[...path]/route.ts`,
    `apps/admin/src/app/operational-dashboard.tsx`,
    `apps/admin/src/app/components/app-analytics-view.tsx`,
    `services/api/modules/catalog/support_point_views.py`,
    `services/api/modules/catalog/support_point_creation.py`,
    `packages/contracts/openapi/schema.yaml`,
    `packages/contracts/src/api.ts`.
  - Verificação: modal acessível de 5 etapas com cliente administrativo compartilhado `adminMutation`, idempotência de 24h via `Idempotency-Key`, validação de erros `400/401/403/409/429/500`, preservação de dados no formulário em falha e geração exclusiva de rascunhos sem publicação autônoma. Testes do admin (59), web (27) e backend (275) aprovados em 2026-08-05.
