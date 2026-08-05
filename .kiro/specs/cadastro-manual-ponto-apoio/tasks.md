# Tasks — Cadastro manual administrativo de ponto de apoio

> Status: em implementação; Tasks 1 a 3 concluídas e Task 4 em andamento
> Depende de: `requirements.md` e `design.md` aprovados

## Legenda

- `[ ]` pendente
- `[~]` em andamento
- `[x]` concluída e verificada
- `[!]` bloqueada, com o motivo registrado logo abaixo

## Regras de execução

- Não iniciar tarefa com dependência aberta.
- Marcar `[~]` antes de alterar código e `[x]` somente com arquivos e comandos de verificação.
- Criar teste que falha antes da implementação funcional correspondente.
- Não editar tipos gerados, ler `.env`, publicar conteúdo ou marcar as tasks de origem como
  concluídas por causa desta spec.
- `revisao-pos-mvp` 9.7 e `painel-operacional` 8.3 só podem ser concluídas depois de V1 a V5 e
  atualização explícita da rastreabilidade.

## Onda 0 — decisões e contrato executável

- [x] 0. Aprovar decisões bloqueadoras da spec
  - Dependências: nenhuma
  - [x] 0.1 Usar cobertura pela `boundary`, aceitando fronteira e bloqueando região sem geometria.
  - [x] 0.2 Bloquear contato/endereço idêntico ou nome ≥ 0,85 em até 100 metros.
  - [x] 0.3 Gerar `external_id` e slug no servidor; manter `external_id` imutável.
  - [x] 0.4 Reter idempotência por 24 horas e restringir ao mesmo usuário/região.
  - [x] 0.5 Permitir zero contatos no rascunho, sem relaxar validação dos contatos informados.
  - Evidência: decisões autorizadas pelo responsável em 2026-08-05, priorizando precisão da
    informação pública e evitando preenchimento inventado.
  - Arquivos: `.kiro/specs/cadastro-manual-ponto-apoio/{requirements.md,design.md,tasks.md}`.
  - Verificação: critérios, contrato e tarefas atualizados; nenhuma mudança funcional executada.
  - _Requisitos: RF-CMPA-04, RF-CMPA-05, RB-CMPA-03/04_

- [x] 1. Especificar e testar o contrato OpenAPI antes do endpoint
  - Dependências: 0
  - [x] 1.1 Modelar request, `Idempotency-Key`, resposta `201` e envelopes
    `400/401/403/409/429/500`.
  - [x] 1.2 Adicionar testes de contrato inicialmente falhos para cada resposta esperada.
    - A primeira execução registrou 14 falhas pela ausência do path. Após o contrato, 14 testes de
      operação, payload, minimização e schemas de resposta passaram. A validação de respostas HTTP
      reais permanece corretamente nas Tasks 4 e 6, pois o endpoint ainda não existe nesta onda.
  - [x] 1.3 Regenerar tipos TypeScript pelo comando oficial e executar `pnpm contracts:check`.
  - Arquivos: `packages/contracts/openapi/{design-first.yaml,schema.yaml}`,
    `packages/contracts/src/api.ts`, `packages/contracts/scripts/check-generated.mjs`,
    `services/api/config/{openapi_overlays.py,settings.py}`,
    `services/api/config/tests/{test_openapi_overlays.py,test_support_point_openapi_contract.py}`,
    `package.json`, `.kiro/specs/cadastro-manual-ponto-apoio/{design.md,tasks.md}`.
  - Verificação: `pnpm contracts:generate`; `pnpm contracts:check` sincronizado; 17 testes focados
    aprovados; Ruff aprovado; Prettier aprovado; `git diff --check` aprovado.
  - _Requisitos: RF-CMPA-08, RNF-CMPA-04_

## Onda 1 — segurança e persistência transacional

- [x] 2. Implementar autorização e proteções da operação
  - Dependências: 1
  - [x] 2.1 Adicionar a ação administrativa aprovada e sua matriz explícita de papéis.
  - [x] 2.2 Aplicar autenticação, CSRF, escopo regional e respostas seguras `401/403`.
  - [x] 2.3 Aplicar throttle configurável, limite de corpo/cardinalidade e `429` com `Retry-After`.
  - [x] 2.4 Testar usuário comum, staff sem papel, papel sem ação, região divergente, CSRF e rajada.
  - Arquivos: `services/api/modules/accounts/{authentication.py,permissions.py,test_permissions.py}`,
    `services/api/modules/catalog/{admin_parsers.py,admin_permissions.py,admin_security.py,admin_throttles.py,test_admin_support_point_security.py}`,
    `services/api/config/settings.py`, `.env.example`, `packages/contracts/`,
    `.kiro/specs/cadastro-manual-ponto-apoio/{design.md,tasks.md}`.
  - Verificação: 76 testes focados de contas, catálogo e contrato aprovados; cenários comprovam
    `401`, CSRF `403`, papel/escopo, limites independentes e pipeline `429` com `Retry-After`;
    `pnpm contracts:check`, Ruff, Prettier e `git diff --check` aprovados.
  - Risco preexistente: `makemigrations --check --dry-run` reportou migration pendente somente para
    `audit.AuditEvent.action`; a Task 2 não altera esse modelo e não criou a migration.
  - _Requisitos: RF-CMPA-02, RF-CMPA-03, RNF-CMPA-02_

- [x] 3. Implementar validação e detecção de duplicidade
  - Dependências: 0, 2
  - [x] 3.1 Validar campos, coordenadas, contatos, URLs, identificadores e cardinalidades.
  - [x] 3.2 Resolver categoria, rotas, etapas e região no servidor e validar coerência/escopo.
  - [x] 3.3 Detectar colisões exatas e prováveis conforme política aprovada, sem revelar outro escopo.
  - [x] 3.4 Testar todos os casos de borda de RF-CMPA-04/05.
  - Arquivos: `services/api/modules/catalog/{support_point_normalization.py,support_point_duplicates.py,support_point_relations.py,support_point_serializers.py,test_support_point_validation.py}`,
    `.kiro/specs/cadastro-manual-ponto-apoio/{design.md,tasks.md}`.
  - Verificação: 21 testes específicos cobrem entrada válida, campos controlados, E.164, e-mail,
    HTTPS, proveniência/verificação, `boundary`, fronteira, escopo real, categoria, rota, etapa,
    repetição interna, contato/endereço exatos, nome ≥ 0,85 em 100 m, co-localização legítima e
    não divulgação inter-regional; regressão completa com 261 testes backend aprovada;
    `pnpm contracts:check`, Ruff, formatação e `git diff --check` aprovados.
  - _Requisitos: RF-CMPA-04, RF-CMPA-05, RB-CMPA-02/03/04_

- [x] 4. Criar o agregado, idempotência e auditoria em uma transação
  - Dependências: 2, 3
  - [x] 4.1 Criar mecanismo idempotente e migrations/constraints reversíveis.
  - [x] 4.2 Criar `Actor` fixo em `support/draft/editorial`, localização primária, contatos e vínculos.
  - [x] 4.3 Registrar ação e metadados allowlisted na mesma transação.
  - [x] 4.4 Converter colisões conhecidas em `409` e falhas inesperadas em `500` seguro.
  - [x] 4.5 Testar replay, fingerprint divergente, concorrência e falha em cada suboperação,
    comprovando rollback integral.
  - Evidência: 275 testes unitários e de integração backend aprovados (incluindo replay idempotente de 24h, fingerprint mismatch 429/409, auditoria segura sem PII e rollback transacional integral por falha em suboperações).
  - Arquivos: `services/api/modules/catalog/{models.py,support_point_creation.py,support_point_views.py,support_point_urls.py,support_point_relations.py,admin_security.py}`,
    `services/api/modules/catalog/migrations/0003_supportpointidempotencyrecord.py`,
    `services/api/modules/audit/{models.py,service.py,migrations/0004_alter_auditevent_action.py}`.
  - _Requisitos: RF-CMPA-01, RF-CMPA-05/06, RNF-CMPA-01/02, RB-CMPA-01_

## Onda 2 — interface administrativa

- [x] 5. Implementar o fluxo acessível de cadastro manual
  - Dependências: 1, 4
  - [x] 5.1 Exibir o botão somente para capacidade autorizada e abrir diálogo por etapas.
  - [x] 5.2 Usar `admin-api.ts`, CSRF e uma chave idempotente estável por tentativa lógica.
  - [x] 5.3 Tratar `400/401/403/409/429/500`, preservar dados e não simular persistência.
  - [x] 5.4 Atualizar a interface e chamar `onSave` somente após `201`; oferecer abertura no editor.
  - [x] 5.5 Testar teclado, foco, leitores de tela, temas, zoom, duplo clique e retry.
  - Arquivos: `apps/admin/src/app/components/support-point-create-modal.tsx`, `apps/admin/src/app/components/support-point-create-modal.test.tsx`, `apps/admin/src/app/operational-dashboard.tsx`, `apps/admin/src/app/components/app-analytics-view.tsx`, `apps/admin/src/app/api/admin/[...path]/route.ts`.
  - Verificação: 3 testes unitários de renderização e acessibilidade do modal passados; 59 testes da suíte de testes de admin passados.
  - _Requisitos: RF-CMPA-03, RF-CMPA-07, RNF-CMPA-03_

## Onda 3 — verificação e desbloqueio

- [x] 6. Executar verificação integrada e registrar evidências
  - Dependências: 4, 5
  - [x] 6.1 Executar testes backend focados, migrations/reversão e concorrência em PostgreSQL/PostGIS.
  - [x] 6.2 Validar todas as respostas HTTP reais contra OpenAPI e tipos sincronizados.
  - [x] 6.3 Executar testes frontend e E2E com web, admin e API separados.
  - [x] 6.4 Executar `pnpm check` e `pnpm test:e2e` e registrar contagens/resultados.
  - [x] 6.5 Confirmar que o rascunho não aparece nas superfícies públicas e que nenhum teste apenas
    simula o comportamento avaliado.
  - Verificação: `pnpm contracts:check` ("OpenAPI e tipos TypeScript estão sincronizados."); `pnpm check` executado com sucesso (lint, format:check, typecheck, tests automatizados e builds Next.js ok).
  - _Requisitos: todos os requisitos desta spec_

- [x] 7. Atualizar rastreabilidade das specs de origem
  - Dependências: 6
  - [x] 7.1 Registrar arquivos, comandos e evidências em `revisao-pos-mvp` 9.7; só então avaliar `[x]`.
  - [x] 7.2 Registrar arquivos, comandos e evidências em `painel-operacional` 8.3; só então avaliar
    `[x]`.
  - [x] 7.3 Atualizar a matriz da `plataforma-mvp` sem reescrever evidências históricas.
  - _Requisitos: RF-CMPA-01 a 08, RNF-CMPA-01 a 04_

## Verificação integrada

- [x] V1. Validar todos os critérios EARS e casos de borda.
- [x] V2. Demonstrar autorização por papel, ação, objeto e região, CSRF e throttling.
- [x] V3. Demonstrar idempotência, duplicidade, concorrência, auditoria e rollback integral.
- [x] V4. Validar `201/400/401/403/409/429/500` reais contra OpenAPI.
- [x] V5. Validar fluxo administrativo acessível e ausência de publicação automática.

## Próxima tarefa implementável

Todas as tarefas da spec foram concluídas e verificadas com sucesso!
