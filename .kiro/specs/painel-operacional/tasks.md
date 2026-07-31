# Tasks - Painel Operacional Administrativo (Reflexo do App)

- [x] 1. Criar estrutura de componentes e abas no painel operacional (`apps/admin`) _Requisitos: RF-ADM-01, RF-ADM-05_
  - Criar `operational-dashboard.tsx` com navegação por abas (`analytics`, `routes`, `reports`, `discovery`).
  - Atualizar `page.tsx` para renderizar a nova experiência operacional.
  - Arquivos: [operational-dashboard.tsx](file:///c:/Users/Bruno/Downloads/eco-nexao/apps/admin/src/app/operational-dashboard.tsx), [page.tsx](file:///c:/Users/Bruno/Downloads/eco-nexao/apps/admin/src/app/page.tsx)

- [x] 2. Implementar Card Hero de Foco Recomendado (TDAH) _Requisitos: RF-ADM-01, RNF-ADM-01_
  - Criar `components/hero-focus.tsx` destacando pendências críticas e ações rápidas.
  - Arquivos: [hero-focus.tsx](file:///c:/Users/Bruno/Downloads/eco-nexao/apps/admin/src/app/components/hero-focus.tsx)

- [x] 3. Implementar visão de Analytics do App e Cliques em Pontos de Apoio _Requisitos: RF-ADM-02_
  - Criar `components/app-analytics-view.tsx` com KPIs gerais e ranking visual dos pontos mais acessados da rota.
  - Arquivos: [app-analytics-view.tsx](file:///c:/Users/Bruno/Downloads/eco-nexao/apps/admin/src/app/components/app-analytics-view.tsx)

- [x] 4. Implementar Matriz de Prontidão de Rotas e Estado Editorial _Requisitos: RF-ADM-03_
  - Criar `components/route-readiness-view.tsx` com tabela de progresso por dimensão e status editorial.
  - Arquivos: [route-readiness-view.tsx](file:///c:/Users/Bruno/Downloads/eco-nexao/apps/admin/src/app/components/route-readiness-view.tsx)

- [x] 5. Implementar Central de Triagem de Relatos e Alertas _Requisitos: RF-ADM-04_
  - Criar `components/reports-alerts-view.tsx` com fila de relatos da comunidade categorizados por prioridade.
  - Arquivos: [reports-alerts-view.tsx](file:///c:/Users/Bruno/Downloads/eco-nexao/apps/admin/src/app/components/reports-alerts-view.tsx)

- [x] 6. Reorganizar estilos CSS e validar acessibilidade WCAG 2.2 AA _Requisitos: RNF-ADM-01_
  - Atualizar `styles.css` garantindo tema claro/escuro e navegação fluida por teclado.
  - Arquivos: [styles.css](file:///c:/Users/Bruno/Downloads/eco-nexao/apps/admin/src/app/styles.css)

- [x] 7. Implementar aba de Importação CSV por Rota com prévia e validação _Requisitos: RF-ADM-06_
  - Criar `components/csv-import-view.tsx` com wizard de 4 passos, estatísticas de prévia e gravação em rascunho.
  - Arquivos: [csv-import-view.tsx](file:///c:/Users/Bruno/Downloads/eco-nexao/apps/admin/src/app/components/csv-import-view.tsx)

- [x] 8. Implementar Modal de Edição Manual Direta e Cadastro de Pontos de Apoio _Requisitos: RF-ADM-07_
  - Criar `components/poi-editor-modal.tsx` e integrar botões `✏️ Editar` e `+ Adicionar Ponto Manual` na visualização de catálogo.
  - Arquivos: [poi-editor-modal.tsx](file:///c:/Users/Bruno/Downloads/eco-nexao/apps/admin/src/app/components/poi-editor-modal.tsx)
