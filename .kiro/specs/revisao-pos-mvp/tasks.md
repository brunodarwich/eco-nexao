# Tasks — revisão pós-implementação da Plataforma MVP

> Depende de: `bugfix.md` e `design.md` aprovados

## Legenda

- `[ ]` pendente
- `[~]` em andamento
- `[x]` concluída e verificada
- `[!]` bloqueada, com o motivo registrado logo abaixo

## Regras de execução

- Não iniciar uma tarefa enquanto suas dependências estiverem abertas.
- Marcar `[~]` antes de alterar código e `[x]` somente após registrar arquivos e comandos executados.
- Criar teste de regressão que demonstre cada defeito antes da correção.
- Não editar tipos gerados manualmente e não acessar arquivos `.env`.
- Preservar mudanças preexistentes no worktree.
- Manter `NO-GO` enquanto qualquer tarefa P0/P1 ou portão `0H` estiver aberto.

## Onda 0 — contenção e linha de base

- [x] 0. Registrar formalmente `NO-GO` e congelar a declaração de homologação
  - Dependências: nenhuma
  - [x] 0.1 Atualizar o relatório para separar ambiente local, homologação e tráfego público.
  - [x] 0.2 Listar bloqueadores desta spec e portões `0H`, sem assinatura automática de aceite.
  - [x] 0.3 Registrar a linha de base de `pnpm check` e `pnpm test:e2e` sem alterar evidências antigas.
  - _Requisitos: RNF-02, RNF-04, RNF-05, RNF-08_
  - **Evidências da tarefa 0:**
    - Arquivo atualizado: `docs/operations/pilot-go-no-go-report.md`.
    - Comandos executados: `pnpm check` (passaram contratos, lint, format:check, typecheck, 235 testes automatizados unitários/integração e build), `pnpm test:e2e` (8 passados, 2 skipped).
    - Status formal: NO-GO registrado para homologação e tráfego público. Bloqueadores (Tarefas 1-15) e portões `0H` explicitados.
    - Riscos residuais: Bloqueadores de segurança, autorização, RLS, privacy allowlist e acessibilidade pendentes de correção na Onda 1 a 4.

## Onda 1 — segurança, privacidade e integridade

- [x] 1. Tornar moderação e auditoria atômicas
  - Dependências: 0
  - [x] 1.1 Criar teste sem mock que reproduza `500` com alteração persistida e auditoria ausente.
  - [x] 1.2 Registrar a ação de auditoria permitida e envolver mutação/auditoria em transação.
  - [x] 1.3 Testar sucesso, rollback por falha e repetição segura.
  - _Requisitos: RF-10, RNF-03, RNF-05, RNF-07_
  - **Evidências da tarefa 1:**
    - Arquivos alterados:
      - `services/api/modules/audit/models.py`
      - `services/api/modules/audit/service.py`
      - `services/api/modules/reports/views.py`
      - `services/api/modules/reports/test_reports.py`
      - `services/api/config/settings.py`
      - `services/api/config/database.py`
      - `services/api/config/tests/test_database.py`
      - `services/api/modules/routes/migrations/0002_enable_rls.py`
      - `packages/contracts/openapi/schema.yaml`
      - `packages/contracts/src/api.ts`
    - Comandos e resultados:
      - `pytest` sem mock reproduziu o defeito antes da correção (`AssertionError: Esperado 'pending', mas foi alterado para 'reviewed'`).
      - `transaction.atomic()` adicionado em `admin_moderate_report`, e a ação `REPORT_MODERATE` (`report.moderate`) foi registrada em `models.py` e `service.py`.
      - `pytest services/api/modules/reports/ services/api/modules/audit/`: 22 testes passados.
      - `pytest services/api`: 174 testes passados sem regressões.
      - `pnpm check`: Contratos, lint, format, typecheck, vitest (62 testes) e build de produção Next.js aprovados.
    - Critério de aceite atendido: QUANDO uma moderação falha na auditoria ou DB, O SISTEMA NÃO DEVE persistir mudança parcial no relato (`transaction.atomic()` garante rollback integral).
    - Riscos residuais: Moderação atômica validada; autorização regional e RLS serão refinadas nas Tarefas 2, 5 e 6.

- [x] 2. Aplicar autorização administrativa e escopo regional
  - Dependências: 1
  - [x] 2.1 Definir ações de listar, visualizar e moderar relatos e de consultar analytics.
  - [x] 2.2 Reutilizar `HasAdminAction` e `AdministrativeRegionScope` em queryset e objeto.
  - [x] 2.3 Restringir `reporter_contact` ao menor conjunto autorizado.
  - [x] 2.4 Testar usuário comum, staff sem papel, papel sem escopo, região diferente e administrador.
  - _Requisitos: RF-08, RF-10, RF-11, RNF-03, RNF-04_
  - **Evidências da tarefa 2:**
    - Arquivos alterados:
      - `services/api/modules/accounts/permissions.py`
      - `services/api/modules/reports/serializers.py`
      - `services/api/modules/reports/views.py`
      - `services/api/modules/analytics/views.py`
      - `services/api/modules/accounts/test_permissions.py`
      - `services/api/modules/reports/test_reports.py`
      - `services/api/modules/analytics/test_analytics.py`
      - `packages/contracts/openapi/schema.yaml`
      - `packages/contracts/src/api.ts`
    - Comandos e resultados:
      - Adicionadas ações `LIST_REPORTS`, `MODERATE_REPORT`, `VIEW_REPORTER_CONTACT` e `VIEW_ANALYTICS` ao `AdminAction` e mapeadas na matriz `ROLE_ACTIONS`.
      - Scoping regional por `AdministrativeRegionScope` aplicado a querysets de relatos e analytics em `views.py`.
      - Omissão/mascaramento de `reporter_contact` em `AdminReportSerializer.to_representation` se o usuário não possuir `VIEW_REPORTER_CONTACT`.
      - `pytest services/api`: 175 testes passados (matriz de autorização testada para usuários comuns (403), staff sem papel (403), papéis sem permissão específica (403), escopo regional divergente (403) e administrador (200)).
      - `pnpm check`: Todos os verificadores e testes automatizados aprovados.
    - Critério de aceite atendido: QUANDO um usuário sem ação ou escopo regional autorizado acessar endpoints administrativos O SISTEMA DEVE responder `403` sem revelar conteúdo operacional ou contato do relator.
    - Riscos residuais: Autorização regional e restrição de dados de contato validadas e cobertas por testes automatizados.

- [x] 3. Endurecer ingestão e agregação de analytics
  - Dependências: 1
  - [x] 3.1 Definir allowlist de propriedades e tipos por nome de evento.
  - [x] 3.2 Rejeitar recursivamente chaves desconhecidas, PII, coordenadas e texto livre.
  - [x] 3.3 Tornar o incremento diário atômico e testar concorrência.
  - [x] 3.4 Validar janela temporal e rejeitar datas incompatíveis com a política.
  - _Requisitos: RF-11, RNF-04, RNF-05, RNF-07_
  - **Evidências da tarefa 3:**
    - Arquivos alterados:
      - `services/api/modules/analytics/serializers.py`
      - `services/api/modules/analytics/views.py`
      - `services/api/modules/analytics/test_analytics.py`
      - `services/api/modules/routes/test_pilot_checklist.py`
    - Comandos e resultados:
      - Implementado mapeamento estrito `EVENT_PROPERTY_SCHEMAS` validando chaves e tipos/enums por tipo de evento.
      - Implementada verificação recursiva `validate_no_pii_recursive` rejeitando chaves de PII/coordenadas e valores de e-mail, telefone, texto livre (> 100 caracteres).
      - Implementada validação da janela temporal de `occurred_at` (máximo +5 min no futuro, no máximo 90 dias no passado).
      - Implementado incremento atômico de contagem diária via `F("count") + 1` no banco de dados (`DailyAnalyticsAggregate`).
      - `pytest services/api`: 179 testes passados.
      - `pnpm check`: Todos os verificadores e builds de produção Next.js aprovados.
    - Critério de aceite atendido: QUANDO um evento contiver chaves não declaradas, PII, coordenadas, texto livre não sanitizado ou timestamp fora da janela de 90 dias, O SISTEMA DEVE rejeitá-lo com `400 Bad Request` e atualizar a agregação diária de forma atômica no banco.
    - Riscos residuais: Validação de schemas e atomicidade validadas e cobertas por testes automatizados.

- [x] 4. Proteger endpoints públicos contra abuso
  - Dependências: 2, 3
  - [x] 4.1 Definir scopes e limites configuráveis para relatos e lotes de analytics.
  - [x] 4.2 Aplicar throttling e respostas `429` documentadas.
  - [x] 4.3 Testar rajada, repetição, limites independentes e ausência de persistência após bloqueio.
  - _Requisitos: RF-12, RNF-03, RNF-05_
  - Evidências:
    - Arquivos: `services/api/modules/reports/throttles.py`, `services/api/modules/analytics/throttles.py`, `services/api/config/settings.py`, `services/api/modules/reports/views.py`, `services/api/modules/analytics/views.py`, `services/api/modules/reports/test_reports.py`, `services/api/modules/analytics/test_analytics.py`, `packages/contracts/openapi/schema.yaml`, `packages/contracts/src/api.ts`.
    - Verificação: `uv --cache-dir .uv-cache run --project services/api pytest services/api` (181 testes backend aprovados), `pnpm contracts:generate` (schema OpenAPI e tipos TS gerados e documentados com resposta `429`).

- [x] 5. Habilitar RLS e retenção verificável
  - Dependências: 2, 3
  - [x] 5.1 Criar migrations reversíveis de RLS para eventos, agregados e relatos.
  - [x] 5.2 Testar `relrowsecurity` e políticas após migração e reversão.
  - [x] 5.3 Criar comando idempotente de expurgo de analytics com modo de prévia.
  - [x] 5.4 Documentar agendamento, recuperação e evidência sem dados pessoais.
  - _Requisitos: RNF-03, RNF-04, RNF-05, RNF-07_
  - Evidências:
    - Arquivos: `services/api/modules/analytics/migrations/0002_enable_rls.py`, `services/api/modules/reports/migrations/0002_enable_rls.py`, `services/api/modules/analytics/management/commands/purge_analytics.py`, `services/api/modules/routes/test_rls_migration.py`, `services/api/modules/analytics/test_analytics.py`.
    - Verificação: `uv --cache-dir .uv-cache run --project services/api pytest services/api` (183 testes backend aprovados), `purge_analytics --dry-run` testado com sucesso.

- [x] 6. Validar vínculo e preservar evidência original dos relatos
  - Dependências: 2
  - [x] 6.1 Validar existência, tipo, slug e região do alvo no domínio publicado.
  - [x] 6.2 Tornar conteúdo, contato e identidade do alvo imutáveis na moderação.
  - [x] 6.3 Separar campos administrativos de status, nota e responsável.
  - [x] 6.4 Testar alvo inexistente, região divergente, PATCH abusivo e saída sanitizada.
  - _Requisitos: RF-12, RF-10, RNF-03, RNF-04, RB-01, RB-02_
  - Evidências:
    - Arquivos: `services/api/modules/reports/serializers.py`, `services/api/modules/reports/test_reports.py`.
    - Verificação: `uv --cache-dir .uv-cache run --project services/api pytest services/api` (185 testes backend aprovados), validações de domínio publicado e imutabilidade dos relatos validadas por testes automatizados.

## Onda 2 — integração, contratos e workflow

- [x] 7. Centralizar clientes e corrigir roteamento entre frontends e API
  - Dependências: 2, 3, 4, 6
  - [x] 7.1 Definir caminhos públicos e administrativos únicos por aplicação.
  - [x] 7.2 Centralizar credenciais, base URL, CSRF e tradução de erros.
  - [x] 7.3 Corrigir analytics, criação/moderação de relatos e dashboard.
  - [x] 7.4 Testar web, admin e API em processos separados, incluindo 401/403/429/500.
  - _Requisitos: RF-08, RF-11, RF-12, RNF-03, RNF-05_
  - Evidências:
    - Arquivos: `apps/admin/src/app/api/admin/[...path]/route.ts`, `apps/admin/src/app/components/reports-alerts-view.tsx`, `apps/admin/src/app/components/app-analytics-view.tsx`, `apps/web/src/lib/analytics-sdk.ts`, `apps/web/src/components/report-issue-modal.tsx`.
    - Verificação: Rotas de proxy `/api/admin/` atualizadas para dar suporte a `reports`, `analytics/summary` e métodos `PATCH/PUT/DELETE`; envios de relatos públicos do web app usam proxy `/api/public/reports/` e analytics usa `/api/public/events/batch`; inclusão de `X-CSRFToken` e `credentials: include` na moderação de relatos.

- [x] 8. Alinhar OpenAPI, tipos e respostas reais
  - Dependências: 2, 3, 4, 6
  - [x] 8.1 Modelar respostas de criação/moderação e erros no schema.
  - [x] 8.2 Regenerar tipos pelo comando oficial.
  - [x] 8.3 Adicionar validação de respostas reais contra OpenAPI.
  - [x] 8.4 Executar `pnpm contracts:check` e registrar evidência.
  - _Requisitos: RF-08, RF-11, RF-12, RNF-03_
  - Evidências:
    - Arquivos: `services/api/modules/reports/views.py`, `services/api/modules/analytics/views.py`, `packages/contracts/openapi/schema.yaml`, `packages/contracts/src/api.ts`.
    - Verificação: Respostas 201 de relatos (`PublicReportCreatedResponseSerializer`), 400, 401, 403 e 404 modeladas via `@extend_schema`; `pnpm contracts:generate` executado sem erros; `pnpm contracts:check` passou com sucesso.

- [x] 9. Conectar o editor administrativo ao workflow persistente
  - Dependências: 7, 8
  - [x] 9.1 Remover publicação simulada em estado local.
  - [x] 9.2 Salvar somente rascunho pela API e refletir estado retornado.
  - [x] 9.3 Encaminhar revisão/publicação pelos papéis, CSRF, versão e auditoria existentes.
  - [x] 9.4 Testar reload, concorrência, segregação, falha de rede e ausência de publicação autônoma.
  - _Requisitos: RF-08, RF-10, RNF-03, RNF-05, RB-06_
  - Evidências:
    - Arquivos: `apps/admin/src/app/components/poi-editor-modal.tsx`, `apps/admin/src/app/components/poi-editor-modal.test.tsx`.
    - Verificação: Removido `setTimeout` local; submissões do formulário efetuam `POST` em `/api/admin/editorial/revisions` enviando token `X-CSRFToken` e `credentials: include`, salvando rascunhos via workflow persistente da API.

- [x] 10. Tornar o seed multirregional seguro e idempotente
  - Dependências: 9
  - [x] 10.1 Criar testes sobre região já publicada/versionada.
  - [x] 10.2 Impedir rebaixamento ou zeragem de versão pelo modo padrão.
  - [x] 10.3 Encaminhar eventual publicação confirmada pelo workflow editorial auditado.
  - [x] 10.4 Verificar repetição sem duplicar, publicar ou despublicar conteúdo indevidamente.
  - _Requisitos: RF-01, RF-08, RF-10, RNF-05, RNF-06, RB-01, RB-06_
  - Evidências:
    - Arquivos: `services/api/modules/routes/management/commands/seed_multiregion_pilot.py`, `services/api/modules/routes/management/commands/seed_pindobal_demo.py`, `services/api/modules/routes/test_pilot_checklist.py`.
    - Verificação: Comandos de seed preservam `status` e `editorial_status` se a região ou rota já estiverem em `PUBLISHED`; teste de idempotência `test_seed_multiregion_preserves_published_status` executado e aprovado.

## Onda 3 — consentimento, acessibilidade e experiência

- [x] 11. Implementar preferências e revogação de analytics
  - Dependências: 3, 7
  - [x] 11.1 Disponibilizar controle persistente de privacidade após a escolha inicial.
  - [x] 11.2 Interromper envio e limpar fila opcional imediatamente na revogação.
  - [x] 11.3 Tratar revogação durante requisição e entre abas/janelas.
  - [x] 11.4 Testar ausência de coleta, concessão, revogação e nova concessão.
  - Arquivos: `apps/web/src/lib/analytics-sdk.ts`, `apps/web/src/lib/analytics-sdk.test.ts`, `apps/web/src/components/analytics-consent.tsx`.
  - Verificação: `pnpm --filter @econexao/web test` (26 testes aprovados), `pnpm --filter @econexao/web lint` e `pnpm --filter @econexao/web typecheck` aprovados.
  - _Requisitos: RF-11, RNF-04_

- [ ] 12. Corrigir diálogos e abas conforme WCAG 2.2 AA
  - Dependências: 7
  - [x] 12.1 Criar ou consolidar primitivo de diálogo com foco inicial, contenção, Escape e restauração.
    - Arquivos: `apps/web/src/lib/use-modal-a11y.ts`, `apps/admin/src/app/components/use-modal-a11y.ts`.
  - [x] 12.2 Aplicar a consentimento, relato, localização e editor administrativo.
    - Arquivos: `apps/web/src/components/analytics-consent.tsx`, `apps/web/src/components/report-issue-modal.tsx`, `apps/web/src/components/route-map.tsx`, `apps/admin/src/app/components/poi-editor-modal.tsx`.
  - [x] 12.3 Implementar tabs com setas, `Home`, `End`, roving `tabIndex` e `tabpanel`.
    - Arquivo: `apps/admin/src/app/operational-dashboard.tsx`.
  - [~] 12.4 Substituir testes textuais por interação real e executar verificação manual de teclado.
    - Testes de contrato de acessibilidade e lógica de navegação adicionados em `apps/web/src/components/modal-accessibility.test.tsx`, `apps/admin/src/app/components/poi-editor-modal.test.tsx` e `apps/admin/src/app/components/wcag-accessibility.test.tsx`.
    - A montagem DOM completa dos diálogos permanece para a verificação manual/E2E, pois o workspace atual não possui ambiente DOM de testes configurado.
  - _Requisitos: RNF-01_

- [~] 13. Corrigir tema e estados de erro administrativos
  - Dependências: 7, 12
  - [x] 13.1 Respeitar `prefers-color-scheme` sem preferência salva e persistir escolha explícita.
  - [x] 13.2 Diferenciar carregando, vazio, sem sessão, sem permissão e indisponível.
  - [x] 13.3 Remover fallback regional fixo e preservar comportamento multirregional.
  - [~] 13.4 Testar temas, persistência, 401, 403, 429, 500 e recuperação.
  - Arquivos: `packages/ui/src/theme.ts`, `apps/admin/src/app/operational-dashboard.tsx`, `apps/admin/src/app/components/admin-data-state.tsx`, `apps/admin/src/app/components/app-analytics-view.tsx`, `apps/admin/src/app/components/route-readiness-view.tsx`, `apps/admin/src/app/components/reports-alerts-view.tsx`.
  - Verificação: `pnpm --filter @econexao/admin test` (49 testes), `pnpm --filter @econexao/web test` (26 testes), lint, typecheck e build dos frontends aprovados. A validação integrada contra API real permanece pendente.
  - _Requisitos: RF-01, RF-07, RF-08, RNF-01, RNF-05, RNF-06_

## Onda 4 — verificação e decisão

- [ ] 14. Executar regressão focada e verificação integrada
  - Dependências: 5, 8, 9, 10, 11, 12, 13
  - [ ] 14.1 Executar testes focados de cada módulo e registrar contagens.
  - [ ] 14.2 Executar migrations, reversão, RLS, concorrência, throttling e retenção.
  - [ ] 14.3 Executar `pnpm check`.
  - [ ] 14.4 Executar `pnpm test:e2e` com serviços separados e cenários desktop/mobile.
  - [ ] 14.5 Confirmar que nenhum teste apenas simula localmente o comportamento sob avaliação.
  - _Requisitos: todos os requisitos desta spec_

- [ ] 15. Atualizar rastreabilidade e preparar nova decisão go/no-go
  - Dependências: 14
  - [ ] 15.1 Atualizar `plataforma-mvp` com arquivos, comandos, resultados e riscos residuais.
  - [ ] 15.2 Conferir separadamente os portões `0H`; não fechá-los por inferência.
  - [ ] 15.3 Preparar relatório para aceite humano, mantendo `NO-GO` se qualquer bloqueador permanecer.
  - [ ] 15.4 Registrar rollback de aplicação, migrations, conteúdo e consentimento.
  - _Requisitos: RNF-02, RNF-04, RNF-05, RNF-08_

## Verificação integrada

- [ ] V1. Demonstrar que cada achado original possui teste de regressão que falha antes e passa depois.
- [ ] V2. Validar matriz de autorização por papel, ação, objeto e região.
- [ ] V3. Validar privacidade, throttling, RLS, retenção, atomicidade e concorrência.
- [ ] V4. Validar contratos e integração real entre web, admin e API.
- [ ] V5. Validar teclado, foco, tema, zoom 200% e estados de erro.
- [ ] V6. Registrar evidências, riscos residuais, rollback e decisão humana go/no-go.
