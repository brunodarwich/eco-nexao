# Tasks - Plataforma MVP ECOnexão

> Status: aprovado e em execução  
> `requirements.md` e `design.md` aprovados para a fundação em 2026-07-27

## Legenda

- `[ ]` pendente
- `[~]` em andamento
- `[x]` concluída e verificada
- `[!]` bloqueada

## Wave 0 - decisões

- [x] 0. Aprovar os requisitos, o design e as pendências arquiteturais
  - Dependências: nenhuma
  - [x] 0.1 Nomear Bruno como responsável interino de produto e privacidade; formalização permanece como portão de homologação
  - [x] 0.2 Confirmar Next.js, estrutura `apps/services/packages`, `pnpm` e `uv`
  - [x] 0.3 Escolher MapLibre, tiles configuráveis, Supabase/PostGIS, mídia S3 compatível e offline mínimo por rota
  - [x] 0.4 Fixar orçamentos iniciais de Web Vitals, disponibilidade e upload
  - _Requisitos: RNF-02, RNF-04, RNF-05_
  - Arquivos: `.kiro/steering/tech.md`, `.kiro/specs/plataforma-mvp/requirements.md`, `design.md`, `spec/01-prd.md`, `spec/03-backend-python-apis.md`
  - Verificação: busca por decisões obsoletas sem ocorrências; `git diff --check`; `pnpm check`

- [ ] 0H. Fechar governança e provedores para homologação
  - Dependências: 5, 7
  - [ ] 0H.1 Formalizar controlador, responsável de privacidade e canal do titular
  - [ ] 0H.2 Contratar e registrar hospedagem da API/frontend, tiles e mídia/CDN
  - [ ] 0H.3 Revalidar orçamentos com a fatia vertical
  - [ ] 0H.4 Aprovar termos, privacidade, orçamento, cotas e credencial restrita de integrações externas
  - _Requisitos: RNF-02, RNF-04, RNF-05, RNF-08_

## Wave 1 - fundação

- [x] 1. Criar o monorepo e a experiência local reproduzível
  - Dependências: 0
  - [x] 1.1 Inicializar PWA, painel, API e pacotes compartilhados
  - [x] 1.2 Configurar lint, formatação, tipos, testes e variáveis por ambiente
  - [x] 1.3 Criar PostgreSQL/PostGIS no Supabase e preparar Redis opcional
    - PostGIS remoto verificado; Redis permanece opcional até a ativação de jobs. GDAL/GEOS continua como pré-requisito explícito da tarefa 3, antes dos modelos GeoDjango.
    - Projeto: `econexao`, `sa-east-1`, ref `hjtkcmbfndbgyurfhsuo`; migration remota `20260727182137_enable_postgis`.
  - [x] 1.4 Documentar setup e validar CI mínima
  - _Requisitos: RNF-03, RNF-05, RNF-07_
  - Arquivos: `apps/`, `services/api/`, `packages/`, `.github/workflows/ci.yml`
  - Verificação: `pnpm check`; consulta `postgis_full_version()` e cálculo espacial no Supabase; configuração documentada em `README.md`

- [x] 2. Implementar tokens, logo, temas e componentes fundamentais
  - Dependências: 0, 1
  - [x] 2.1 Codificar os tokens claro/escuro de `.kiro/steering/design-system.md`
  - [x] 2.2 Implementar bootstrap sem flash e controle acessível persistente
  - [x] 2.3 Criar componentes básicos com estados de foco, erro, vazio e carregamento
  - [x] 2.4 Verificar contraste, teclado e `prefers-reduced-motion`
  - _Requisitos: RF-07, RNF-01_
  - Arquivos: `packages/ui/src/`, `apps/web/src/app/`, `apps/admin/src/app/`
  - Verificação: `pnpm check` (3 testes frontend e 5 backend, lint, tipos e dois builds); navegador em temas claro/escuro e viewport 390x844; persistência e `theme-color`; foco de 3 px; sem overflow ou erros de console; contrastes principais entre 5,4:1 e 16,99:1

- [x] 3. Modelar domínio multirregional e contratos públicos
  - Dependências: 0, 1
  - [x] 3.1 Criar modelos, constraints, índices espaciais e migrations
    - Arquivos: `services/api/modules/{core,regions,routes,catalog}/`, `services/api/config/settings.py`, `.env.example`, `README.md`
    - Verificação: `pnpm check`; `python manage.py check`; `python manage.py makemigrations --check --dry-run`; 23 testes backend; migrations aplicadas no projeto `econexao`; 6 geometrias SRID 4326 com índices GiST; RLS habilitado em 20/20 tabelas Django
    - [x] Habilitar RLS sem políticas públicas nas tabelas Django após diagnóstico do Supabase Security Advisor
  - [x] 3.2 Implementar estados editoriais e regras de publicação
    - Arquivos: `services/api/modules/core/models.py`, `services/api/modules/publishing/rules.py`, `services/api/modules/publishing/test_rules.py`
    - Verificação: `pnpm check`; 22 testes backend, incluindo transições, segregação, validade crítica, referências publicadas, confirmação humana e checksum
  - [x] 3.3 Publicar OpenAPI v1 e gerar tipos do frontend
    - Arquivos: `services/api/modules/{core,regions,routes}/`, `packages/contracts/`, `package.json`, `.github/workflows/ci.yml`
    - Verificação: `pnpm contracts:check`; OpenAPI 3.0.3 validada; tipos TypeScript gerados com `openapi-typescript` 7.13.0; `pnpm check` com 28 testes backend, 3 frontend e dois builds
  - [x] 3.4 Testar isolamento entre regiões e integridade referencial
    - Arquivos: `services/api/modules/{routes,catalog}/models.py`, `services/api/modules/routes/test_{domain_integrity,public_contract}.py`, `services/api/modules/test_domain_models.py`
    - Verificação: `pnpm check`; 33 testes backend, incluindo escopo dinâmico por `region_slug`, proteção contra referências cruzadas entre rota/região/etapa e políticas de exclusão referencial; 3 testes frontend e dois builds
  - _Requisitos: RF-01, RF-02, RF-03, RF-05, RNF-06_

## Wave 2 - primeira fatia vertical

- [x] 4. Entregar seleção de região e descoberta de rotas
  - Dependências: 2, 3
  - [x] 4.1 Implementar resolução por URL, preferência e escolha
  - [x] 4.2 Implementar cards, busca, filtros e estados vazios
  - [x] 4.3 Adicionar metadados, URLs compartilháveis e testes E2E
  - _Requisitos: RF-01, RF-02, RNF-01, RNF-02_
  - Arquivos: `apps/web/src/{app,components,lib}/`, `apps/web/e2e/`, `apps/web/next.config.ts`, `apps/web/playwright.config.ts`
  - Verificação: `pnpm check` (6 testes frontend e 33 backend, lint, formatação, tipos, contratos e dois builds); `pnpm test:e2e` (fluxo de região, filtros e URL de rota aprovado em Chromium desktop e mobile)

- [x] 5. Entregar a rota de Pindobal de ponta a ponta
  - Dependências: 2, 3, 4
  - [x] 5.1 Implementar visão geral, etapas, preparação e alertas
  - [x] 5.2 Implementar mapa com lista textual equivalente e localização opcional
  - [x] 5.3 Implementar catálogo, detalhe do ator e contatos externos
  - [x] 5.4 Popular dados controlados de Pindobal e executar roteiro E2E
  - [x] 5.5 Exibir atores publicados como pins agrupados, filtros e lista equivalente na aba de mapa
    - Referência visual: protótipo local `rota-pindobal-interativa.html`, preservando a arquitetura MapLibre e a separação de conteúdo Google.
    - Verificar carregamento paralelo, filtros sincronizados, agrupamentos, popup seguro, teclado, temas e estado sem pontos publicados.
    - _Requisitos: RF-04, RF-05, RF-13, RNF-01, RNF-02, RNF-08_
    - Arquivos: `apps/web/src/components/{route-map.tsx,route-experience.tsx}`, `apps/web/src/lib/route-map-points.ts`, `apps/web/src/app/styles.css`, `apps/web/src/app/discovery.test.ts`, `apps/web/e2e/discovery.spec.ts`, `.kiro/specs/plataforma-mvp/{requirements.md,design.md,tasks.md}`
    - Verificação: `pnpm --filter @econexao/web typecheck`; `pnpm --filter @econexao/web test` (16 testes); `pnpm --filter @econexao/web lint`; `pnpm --filter @econexao/web build`; inspeção Playwright da build de produção em desktop, tema escuro e viewport móvel de 390 px, sem erros de console, overlay ou overflow horizontal. Evidências visuais: 2 atores publicados; pins sobre as etapas e com prioridade de clique; filtro `Alimentação` com `aria-pressed=true`, lista reduzida para 1 item e fonte renderizada sem o pin de Apoio; alternativa textual preservada.
  - _Requisitos: RF-03, RF-04, RF-05, RNF-01_
  - Arquivos: `apps/web/src/{app,components,lib}/`, `services/api/modules/{core,routes}/`, `packages/contracts/`, `README.md`
  - Verificação: `pnpm check` (9 testes frontend e 34 backend, contratos, lint, formatação, tipos e dois builds); `pnpm test:e2e` (card → rota → mapa/lista → catálogo → contato aprovado em Chromium desktop e mobile); `pnpm seed:pindobal` idempotente; banco de desenvolvimento com 1 região, 1 rota, 3 etapas, 2 segmentos e 2 atores demonstrativos publicados

- [x] 5A. Descobrir candidatos próximos de Pindobal pelo Google Maps
  - Dependências: 3, 5
  - [x] 5A.1 Implementar cliente e comando de prévia efêmera para a Places API (New)
  - [x] 5A.2 Proteger credencial, validar parâmetros e testar sem rede real
  - [x] 5A.3 Persistir execuções e Place IDs de forma idempotente, sem conteúdo Google
  - [x] 5A.4 Executar a consulta real, registrar referências e exibir a prévia atribuída
    - Execução real concluída em 29/07/2026 com 20 resultados e prévia efêmera atribuída. A repetição idempotente deixou 3 execuções históricas, 20 referências únicas e 60 ocorrências; nenhuma referência foi ligada a `Actor`.
    - Place IDs salvos: `ChIJ6_hIAVFTiJIRzDfIDeGOvQ0`, `ChIJ69wQs8ZTiJIRqmX1nerPyW4`, `ChIJ86xQK_dTiJIR2d2lvhF11zg`, `ChIJ8VdQoodSiJIR40I42YflUL4`, `ChIJ9Ry3nYdSiJIRw-pxHxE7u30`, `ChIJa2e_74NSiJIRA-3IKKTGpMs`, `ChIJEbPs9X1SiJIRLT_Cy8fVETs`, `ChIJf0ZXs6ZTiJIRNWCEXPqgYq0`, `ChIJG8tEvvRTiJIRVwrgtCxCmoU`, `ChIJgWMSYodTiJIRebReEt-IrZU`, `ChIJHwuyajNTiJIRVFgAUgfYT4M`, `ChIJjRzeC31SiJIRLYAFCDTC8a0`, `ChIJKfh-VjNTiJIReXrSQi7M_A4`, `ChIJL0eQW4RSiJIRY7Gz-x478uo`, `ChIJOS_Bz8NSiJIRyPtI4f6Ktcg`, `ChIJP6tpkKj5iJIRzwsYshrA5vs`, `ChIJq5Brgw2ziZIRvzEvDxnPeT8`, `ChIJRS7nwXytiZIRnqNxeGoXt7w`, `ChIJXer8vn1SiJIRLeG7mEpbXzc`, `ChIJXfyOyYdSiJIRA1lF7kMc7FI`.
  - [x] 5A.5 Preparar saída offline baseada somente em conteúdo editorial próprio verificado
  - _Requisitos: RF-05, RF-08, RF-13, RNF-03, RNF-05_
  - Arquivos: `services/api/modules/catalog/{google_places.py,external_discovery.py,models.py,migrations/0002_external_discovery.py,management/commands/search_google_places_pindobal.py}`, `services/api/modules/routes/test_public_contract.py`, `apps/web/src/app/offline.test.ts`, `spec/08-google-places-curadoria.md`, `.env.example`, `README.md`
  - Verificação: `uv --cache-dir .uv-cache run --project services/api pytest services/api/modules/routes/test_public_contract.py services/api/modules/catalog/test_google_places.py` (18 testes); `pnpm check` (13 testes da PWA, 1 do painel, 51 do backend, contratos, lint, formatação, tipos e dois builds); contrato e pacote offline rejeitam relações externas, Place IDs e recursos fora da ECOnexão; `pnpm discover:pindobal` concluiu a execução `5d6b7bce-9ad9-4faf-b6c9-102ab37c8360` com 20 Place IDs e prévia completa em terminal `cp1252`; consulta ORM confirmou 3 `ExternalDiscoveryRun`, 20 `ExternalSourceReference` e 60 `ExternalDiscoveryHit`, sem vínculo a `Actor` e sem campos Google persistíveis nos modelos

- [x] 6. Implementar preferências locais e offline seletivo
  - Dependências: 4, 5
  - [x] 6.1 Persistir favoritos e preferências sem conta
  - [x] 6.2 Gerar manifesto/pacote versionado por rota
  - [x] 6.3 Implementar download, progresso, atualização e remoção
  - [x] 6.4 Testar perda de rede, pacote vencido e falha de armazenamento
  - _Requisitos: RF-06, RNF-05_
  - Arquivos: `apps/web/src/{app/manifest.ts,app/offline.test.ts,components/route-local-actions.tsx,lib/offline-package.ts,lib/offline-storage.ts}`, `apps/web/public/sw.js`, `apps/web/e2e/discovery.spec.ts`, `README.md`
  - Verificação: `pnpm check` (13 testes frontend, 1 do painel, 40 backend, contratos, lint, formatação, tipos e dois builds); `pnpm test:e2e` (desktop e mobile com download, navegação offline e persistência de favorito); `pnpm seed:pindobal`

## Wave 3 - operação

- [x] 7. Implementar autenticação, papéis e autorização administrativa
  - Dependências: 1, 3
  - [x] 7.1 Configurar sessão e proteção CSRF
    - Arquivos: `services/api/modules/accounts/`, `services/api/config/{settings.py,urls.py}`, `.env.example`, `packages/contracts/`
    - Verificação: `pnpm check` (51 testes backend, 13 da PWA, 1 do painel, contratos, lint, formatação, tipos e dois builds); testes cobrem bootstrap CSRF, bloqueio sem token, login administrativo, sessão, logout protegido e rejeição genérica de usuário não administrativo
  - [x] 7.2 Implementar papéis e autorização por ação/objeto
    - Arquivos: `services/api/modules/accounts/{models.py,permissions.py,serializers.py,views.py,migrations/0001_administrative_region_scope.py}`, `packages/contracts/`, `.kiro/specs/plataforma-mvp/design.md`
    - Verificação: 16 testes do módulo `accounts`; `makemigrations --check --dry-run`; contrato OpenAPI regenerado com papéis, ações e regiões autorizadas na identidade administrativa
  - [x] 7.3 Testar matriz de permissões e tentativas de escalada
    - Arquivos: `services/api/modules/accounts/test_{auth,permissions}.py`
    - Verificação: `pnpm check` (62 testes backend, 13 da PWA, 1 do painel, contratos, lint, formatação, tipos e dois builds); matriz completa e tentativas de elevação por papel, `superuser`, região e ausência de declaração negadas; migration aplicada no banco de desenvolvimento com 5 grupos e RLS ativo na tabela de escopos
  - _Requisitos: RF-08, RF-10, RNF-03_

- [x] 8. Implementar fluxo editorial, publicação e rollback
  - Dependências: 3, 7
  - [x] 8.1 Criar edição, diff, envio, devolução e aprovação
    - Arquivos: `services/api/modules/publishing/{models.py,workflow.py,serializers.py,views.py,urls.py,migrations/0001_editorial_revision.py,test_workflow.py}`, `services/api/config/{settings.py,urls.py}`, `packages/contracts/`, `.kiro/specs/plataforma-mvp/design.md`
    - Verificação: `pnpm check` (71 testes backend, 13 da PWA, 1 do painel, contratos, lint, formatação, tipos e dois builds); testes cobrem diff determinístico, limite de 256 KiB, trava otimista, estados, motivo de devolução, imutabilidade e segregação entre envio/aprovação; migration aplicada no banco de desenvolvimento com RLS ativo
  - [x] 8.2 Implementar publicação atômica e bloqueios de dados críticos
    - Arquivos: `services/api/modules/publishing/{models.py,publication.py,serializers.py,views.py,urls.py,migrations/0002_publication_version.py,test_publication.py}`, `packages/contracts/`, `.kiro/specs/plataforma-mvp/design.md`
    - Verificação: `pnpm check` (79 testes backend, 13 da PWA, 1 do painel, contratos, lint, formatação, tipos e dois builds); testes cobrem allowlist completa, checksum/versão imutável, idempotência estrutural, transação, segregação, fonte, confirmação humana, justificativa crítica e referências de região/rota/ator; migration aplicada no banco de desenvolvimento com RLS ativo, sem executar publicação
  - [x] 8.3 Implementar restauração como nova versão
    - Arquivos: `services/api/modules/publishing/{models.py,publication.py,serializers.py,views.py,urls.py,migrations/0003_publicationversion_restored_from_and_more.py,test_publication.py}`, `packages/contracts/`, `.kiro/specs/plataforma-mvp/design.md`
    - Verificação: `pnpm check` (82 testes backend, 13 da PWA, 1 do painel, contratos, lint, formatação, tipos e dois builds); migration aplicada no banco de desenvolvimento; RLS confirmado ativo; testes cobrem histórico imutável, versão de origem, concorrência, justificativa, confirmações, revalidação e segregação
  - [x] 8.4 Registrar e testar auditoria de ações críticas
    - Arquivos: `services/api/modules/audit/`, `services/api/modules/{accounts,publishing}/`, `services/api/config/{settings.py,urls.py}`, `packages/contracts/`, `.kiro/specs/plataforma-mvp/design.md`
    - Verificação: `pnpm check` (89 testes backend, 13 da PWA, 1 do painel, contratos, lint, formatação, tipos e dois builds); migration aplicada no banco de desenvolvimento com RLS ativo; smoke test transacional de persistência aprovado e integralmente revertido; testes cobrem imutabilidade, allowlist, `request_id`, escopo regional, permissões, login, logout, aprovação, publicação e restauração
  - [x] 8.5 Implementar prévia Google Places autenticada, atribuída, efêmera, separada do MapLibre e protegida por feature flag
    - A ativação com resultados reais depende de 0H.4 e da revisão vigente de `spec/08-google-places-curadoria.md`.
    - Arquivos: `services/api/modules/catalog/{admin_discovery.py,admin_serializers.py,admin_throttles.py,admin_urls.py,admin_views.py,test_admin_discovery.py}`, `services/api/modules/audit/`, `apps/admin/src/`, `packages/contracts/`, `.env.example`, `README.md`, `spec/08-google-places-curadoria.md`, `.kiro/specs/plataforma-mvp/design.md`
    - Verificação: `pnpm check` (94 testes backend, 13 da PWA, 2 do painel, contratos, lint, formatação, tipos e dois builds); migration aplicada com RLS ativo; testes cobrem feature flag desativada, permissão e escopo regional, throttle, limites de custo, erro seguro, auditoria sem payload, persistência exclusiva de Place IDs, resposta `no-store`, efemeridade, atribuição oficial e ausência de MapLibre
  - _Requisitos: RF-08, RF-10, RF-13, RNF-05, RNF-07, RNF-08_

- [x] 9. Implementar importação CSV com preview
  - Dependências: 3, 7, 8
  - [x] 9.1 Validar arquivo contra o schema de `spec/schemas/catalogo-template.csv`
    - Arquivos: `services/api/modules/imports/catalog_csv.py`, `relations.py`, `serializers.py`, `throttles.py`, `views.py`, `urls.py`, `test_catalog_csv.py`, `test_views.py`, `services/api/config/settings.py`, `services/api/config/urls.py`, `.env.example`, `packages/contracts/openapi/schema.yaml`, `packages/contracts/src/api.ts`
    - Verificação: `pnpm check` (101 testes backend, 13 da PWA, 2 do painel, contratos, lint, formatação, tipos e dois builds); `python services/api/manage.py makemigrations --check --dry-run` (`No changes detected`)
    - Evidências: template oficial UTF-8 aceito; cabeçalho e ordem exatos; limite de 10 MiB/10.000 linhas; tipos, enums, datas, coordenadas, E.164, e-mail, HTTPS, consentimento, mídia e proveniência validados; relações limitadas ao escopo regional; duplicidade no arquivo detectada; endpoint multipart autenticado, limitado, sem retenção e `no-store`
  - [x] 9.2 Produzir relatório por linha/coluna e preview das mudanças
    - Arquivos: `services/api/modules/imports/{catalog_csv.py,relations.py,serializers.py,views.py,test_catalog_csv.py,test_views.py}`, `services/api/modules/routes/test_public_contract.py`, `packages/contracts/`, `.kiro/specs/plataforma-mvp/design.md`
    - Verificação: 104 testes backend; 13 testes da PWA e 2 do painel; 16 testes focados de importação/contrato público; OpenAPI e tipos sincronizados; lint, formatação Python, tipos e dois builds aprovados
    - Evidências: resposta `no-store` expõe relatório com severidade, linha, coluna, código e orientação; arquivo válido recebe contagens e prévia por linha para `create`, `update` e `archive`; erro ou relatório truncado remove a prévia; arquivamento sem alvo e identificador fora do escopo são bloqueados sem revelar conteúdo de outra região; nenhuma escrita de domínio é executada
  - [x] 9.3 Aplicar lote idempotente somente como rascunho
    - Arquivos: `services/api/modules/imports/{models.py,commit.py,serializers.py,views.py,urls.py,migrations/0001_initial.py,test_commit.py,test_views.py}`, `services/api/modules/audit/{models.py,service.py,migrations/0003_alter_auditevent_action.py}`, `packages/contracts/`, `.kiro/specs/plataforma-mvp/design.md`
    - Verificação: `pnpm check` (109 testes backend, 14 da PWA, 2 do painel, contratos, lint, formatação, tipos e dois builds); 26 testes focados de importação/auditoria/contrato público; `makemigrations --check --dry-run` sem alterações
    - Evidências: commit exige arquivo, hash, UUID idempotente e confirmação explícita; repetição devolve o lote existente sem duplicar rascunhos ou auditoria; hash divergente e relações alteradas bloqueiam a transação; linhas são persistidas somente como `CatalogImportDraft` privado, sem alterar `Actor` ou conteúdo publicado; auditoria usa allowlist sem payload; migrations `audit.0003` e `imports.0001` aplicadas no banco de desenvolvimento, com RLS ativo nas duas novas tabelas
  - [x] 9.4 Testar arquivo grande, duplicado, malformado e relações inválidas
    - Arquivos: `services/api/modules/imports/test_catalog_csv.py`
    - Verificação: suíte do módulo de importação com arquivo acima de 10 MiB, 10.001 linhas,
      identificadores duplicados, CSV malformado e relações inválidas; nenhuma prévia parcial.
  - [x] 9.5 Adequar o inventário histórico e operacional de Santarém–Pindobal
    - [x] 9.5.1 Unir as duas fontes sem duplicar as 195 linhas compartilhadas
    - [x] 9.5.2 Converter registros elegíveis ao schema oficial e colocar proveniência Google em quarentena
    - [x] 9.5.3 Gerar relatório de duplicidades, bloqueios e revisão manual
    - [x] 9.5.4 Conectar o wizard administrativo aos endpoints reais de validação e commit
    - Arquivos: `services/api/modules/imports/{pindobal_inventory.py,test_pindobal_inventory.py,management/commands/adapt_pindobal_inventory.py}`, `apps/admin/src/app/{components/csv-import-view.tsx,components/csv-import-view.test.tsx,operational-dashboard.tsx,operational-dashboard.test.tsx}`, `outputs/pindobal-inventory/`, `README.md`
    - Verificação: 195 linhas reconciliadas sem inflação, 181 rascunhos canônicos, 14 candidatos
      Google em quarentena, nenhuma duplicidade forte e 9 pares com contato compartilhado; CSV
      canônico aceito pelo validador oficial; `pytest services/api/modules/imports` (20 testes),
      painel (41 testes), TypeScript, lint direcionado e build Next.js aprovados.
    - _Requisitos: RF-09, RF-13, RNF-03, RNF-05_
  - _Requisitos: RF-09, RNF-03, RNF-05_

- [ ] 10. Implementar relatos de informação incorreta
  - Dependências: 5, 7, 8
  - [ ] 10.1 Criar formulário público protegido contra abuso
  - [ ] 10.2 Vincular relato ao registro e à fila editorial
  - [ ] 10.3 Testar moderação, limites e ausência de publicação automática
  - _Requisitos: RF-12, RNF-03_

## Wave 4 - medição e expansão

- [ ] 11. Implementar consentimento, ingestão e dashboard de analytics
  - Dependências: 5, 7
  - [ ] 11.1 Implementar preferências e fila local por finalidade
  - [ ] 11.2 Criar endpoint em lote com allowlist e rejeição de PII
  - [ ] 11.3 Criar agregações e dashboard com proteção contra reidentificação
  - [ ] 11.4 Testar ausência de coleta, revogação, retenção e payloads proibidos
  - _Requisitos: RF-11, RNF-04, RNF-07_

- [ ] 12. Publicar cinco rotas e validar o modelo multirregional
  - Dependências: 6, 8, 9, 11
  - [ ] 12.1 Carregar e revisar as quatro rotas adicionais
  - [ ] 12.2 Criar uma região não pública de teste sem alteração de código
  - [ ] 12.3 Executar checklist editorial, acessível, offline e analítico
  - _Requisitos: RF-01 a RF-13, RNF-01 a RNF-08_

## Verificação integrada

- [ ] V1. Validar todos os critérios de aceite e a matriz de rastreabilidade
- [ ] V2. Executar testes automatizados, acessibilidade manual e teste mobile em rede limitada
- [ ] V3. Ensaiar backup, rollback de aplicação, rollback de conteúdo e resposta a incidente
- [ ] V4. Registrar evidências, riscos residuais e decisão de go/no-go do piloto
