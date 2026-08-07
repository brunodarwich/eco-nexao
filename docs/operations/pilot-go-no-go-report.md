# Relatório de Go/No-Go do Piloto, Riscos Residuais e Evidências — V8

**Projeto:** Plataforma ECOnexão (MVP multirregional — piloto Pindobal/Santarém-Alter do Chão)
**Data da avaliação:** 6 de agosto de 2026
**Responsável por produto e tecnologia:** Bruno (interino)
**Decisão integrada:** **NO-GO — V1 bloqueada e portões externos abertos**

## 1. Resumo executivo e separação por ambiente

A revisão pós-implementação identificou achados de segurança, integridade transacional,
privacidade, integração frontend/API, acessibilidade e governança. A regressão focada de backend e
componentes passa. A execução V1 encontrou e corrigiu falhas no teste de persistência de tema e no
tratamento administrativo de erros/retry; a suíte completa agora passa. A integração real entre
serviços, porém, não iniciou sem a referência explícita do Supabase autorizado. Os portões externos
`0H` e o aceite humano também continuam abertos. A decisão permanece **NO-GO**.

1. **Desenvolvimento local:** permitido para implementação e verificação orientadas pelas specs.
2. **Homologação/staging:** **NO-GO** até conclusão verificada de `revisao-pos-mvp`, fechamento dos
   portões aplicáveis e aceite humano.
3. **Tráfego público:** **NO-GO** enquanto houver bloqueador técnico, operacional ou de governança.

## 2. Estado técnico e portões

### A. Spec `revisao-pos-mvp`

| Tarefas     | Estado em 06/08/2026 | Observação                                                                                           |
| ----------- | -------------------- | ---------------------------------------------------------------------------------------------------- |
| T-01 a T-06 | concluídas na spec   | confirmadas pela regressão backend focada de V1                                                      |
| T-07        | em andamento         | cliente e proxy corrigidos; 7.4 aguarda reexecução no Supabase/PostGIS explicitamente autorizado     |
| T-08 a T-12 | concluídas na spec   | contratos, workflow, seed, consentimento e acessibilidade possuem evidências nas respectivas tarefas |
| T-13 e T-14 | concluídas na spec   | falhas reproduzidas pela V1 foram corrigidas; `pnpm check` e 40 E2E aplicáveis passam                |
| T-15        | pendente             | rastreabilidade final, riscos residuais, rollback e preparação do aceite humano                      |

O cadastro manual de ponto de apoio passou a usar operação transacional e cria somente rascunho.
A interface continua sem inferir prontidão ou ranking a partir de campos públicos ausentes; esses
indicadores dependem dos contratos administrativos auditáveis.

### B. Portões externos de homologação (`0H`)

- **0H-1 — privacidade e governança:** formalizar controlador, responsável por privacidade e canal
  do titular.
- **0H-2 — infraestrutura:** contratar e registrar hospedagem da API/frontend, tiles e mídia/CDN.
- **0H-3 — desempenho em campo:** validar LCP, INP e CLS em condições reais do piloto.
- **0H-4 — Google Places:** aprovar termos, credencial restrita, cotas, orçamento e atribuição antes
  de ativação externa.

## 3. Matriz de verificação

| Etapa | Descrição                                             | Estado    | Observação                                                                                                                  |
| ----- | ----------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------- |
| V1    | rastreabilidade e regressões por achado               | bloqueada | matriz completa registrada em `revisao-pos-mvp/tasks.md`; falta reexecutar a integração real no Supabase/PostGIS autorizado |
| V2    | autorização por papel, ação, objeto e região          | pendente  | testes focados existem; falta validação integrada                                                                           |
| V3    | privacidade, throttling, RLS, retenção e concorrência | pendente  | suíte Django passa; falta ensaio integrado de migrations/RLS                                                                |
| V4    | contratos e integração real web/admin/API             | pendente  | contratos sincronizados; serviços separados ainda pendentes                                                                 |
| V5    | teclado, foco, tema, zoom e estados de erro           | pendente  | evidência E2E de V1 passa; fechamento formal de V5 ainda não executado                                                      |
| V6    | riscos residuais, rollback e decisão humana           | pendente  | agentes não assinam GO                                                                                                      |

## 4. Evidências

### Verificação V1 — 06/08/2026

- Matriz achado → requisito → código → teste → resultado registrada em
  `.kiro/specs/revisao-pos-mvp/tasks.md`, incluindo o mecanismo pelo qual cada teste detecta o
  comportamento incorreto.
- Nenhum código de produção foi temporariamente alterado para demonstrar sensibilidade.
- `pnpm --filter @econexao/web test`: 27/27 aprovados.
- `pnpm --filter @econexao/admin test`: 65/65 aprovados.
- Regressão backend focada: 84/84 aprovados, cobrindo relatos, analytics, RLS em migrations,
  contratos OpenAPI, seed e publicação.
- `pnpm contracts:check`: aprovado; OpenAPI e tipos TypeScript sincronizados.
- O primeiro E2E focado reproduziu 10 falhas: comparação inválida de `localStorage` entre origens,
  ausência de renderização de `summaryError` e retry que não refazia a requisição do resumo.
- Correções em `operational-dashboard.tsx`, `admin-api.ts`, seu teste unitário e no E2E. O painel
  agora diferencia `401`, `403`, `429` e `502`, mantém o erro até a recuperação e confirma a
  segunda requisição; o teste de tema usa nova aba da mesma origem.
- `pnpm check`: aprovado com contratos, lint, formatação, tipos, 27 testes web, 65 admin, 284
  backend (1 ignorado) e dois builds.
- `pnpm test:e2e`: 40 aprovados e 2 ignorados. Os 32 cenários de WCAG e tema/erros passaram em
  desktop e mobile; os ignorados dependem de conteúdo publicado pela API local.
- `pnpm test:integration:services`: bloqueado antes de iniciar os serviços porque
  `TASK_7_4_SUPABASE_PROJECT_REF` não foi fornecida. Nenhuma credencial foi inferida ou lida.
- Reds históricos preservados: rollback atômico detectou `reviewed` onde deveria permanecer
  `pending`; integração separada detectou `404`/`301` antes da correção. A segunda execução foi
  formalmente substituída na tarefa 7.4 por não usar a arquitetura Supabase/PostGIS aprovada.
- Conclusão: todos os achados foram mapeados a testes e as regressões locais passam, mas o achado de
  roteamento ainda não possui resultado pós-correção aceito na arquitetura Supabase/PostGIS. V1
  permanece `[!]` e a decisão permanece **NO-GO**.

### Verificação atual — 05/08/2026

- `pnpm check`: aprovado integralmente fora do sandbox com o Python 3.13 configurado.
- Contratos OpenAPI/tipos, ESLint, Ruff, Prettier, typecheck e builds: aprovados.
- Backend Django: 187 testes aprovados.
- Web: 5 arquivos e 27 testes aprovados.
- Admin: 14 arquivos e 56 testes aprovados.
- E2E público: os dez cenários chegaram ao resultado observável de 8 aprovados e 2 ignorados em
  desktop/mobile, mas o processo Playwright não encerrou antes do limite externo de 240 segundos.
  Isso não substitui nem fecha o E2E com web, admin e API em serviços separados.

### Linha de base histórica — 31/07/2026

A linha de base V5 registrou `pnpm check` completo, 173 testes Django, 21 testes web, 41 testes
admin e oito cenários E2E aprovados, com dois ignorados. Esses números são preservados como
evidência histórica e não substituem a regressão exigida depois das mudanças atuais.

## 5. Governança e declaração de aceite

Agentes e sistemas automatizados podem preparar evidências, mas não podem converter a decisão para
GO. Homologação e produção exigem fechamento técnico, análise separada dos portões `0H` e aceite
humano explícito.

**Estado atual:** **NO-GO — V1 BLOQUEADA, VERIFICAÇÕES V2–V6 E PORTÕES 0H ABERTOS**
_Revisado em 06/08/2026._
