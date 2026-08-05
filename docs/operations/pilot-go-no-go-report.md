# Relatório de Go/No-Go do Piloto, Riscos Residuais e Evidências — V7

**Projeto:** Plataforma ECOnexão (MVP multirregional — piloto Pindobal/Santarém-Alter do Chão)
**Data da avaliação:** 5 de agosto de 2026
**Responsável por produto e tecnologia:** Bruno (interino)
**Decisão integrada:** **NO-GO — correções e verificação ainda abertas**

## 1. Resumo executivo e separação por ambiente

A revisão pós-implementação identificou achados de segurança, integridade transacional,
privacidade, integração frontend/API, acessibilidade e governança. Os seeds, a revogação de
analytics, o tema inicial e os estados de erro foram corrigidos e a suíte integrada automatizada
passa. A integração real entre serviços, a validação de respostas contra OpenAPI, a validação
manual de acessibilidade, os portões externos `0H` e o aceite humano continuam abertos. A decisão
permanece **NO-GO**.

1. **Desenvolvimento local:** permitido para implementação e verificação orientadas pelas specs.
2. **Homologação/staging:** **NO-GO** até conclusão verificada de `revisao-pos-mvp`, fechamento dos
   portões aplicáveis e aceite humano.
3. **Tráfego público:** **NO-GO** enquanto houver bloqueador técnico, operacional ou de governança.

## 2. Estado técnico e portões

### A. Spec `revisao-pos-mvp`

| Tarefas     | Estado em 05/08/2026                           | Observação                                                                                                                |
| ----------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| T-01 a T-06 | concluídas na spec                             | confirmadas pela suíte automatizada atual                                                                                  |
| T-07 e T-08 | parcialmente concluídas                        | clientes/schema corrigidos; integração com serviços separados e validação de respostas reais contra OpenAPI estão abertas |
| T-09        | parcialmente concluída, com bloqueio explícito | edição de ator existente usa workflow real; cadastro manual de ator novo não possui contrato/endpoint e continua pelo CSV |
| T-10 e T-11 | concluídas na spec                             | aguardam confirmação conjunta na regressão integrada                                                                      |
| T-12        | aberta                                         | hook modal unificado; interação real de teclado e verificação manual ainda faltam                                         |
| T-13        | em andamento                                   | estados principais implementados; testes integrados de tema e erros ainda faltam                                          |
| T-14        | pendente                                       | `pnpm check` passou; migrations em ambiente integrado, acessibilidade e E2E com serviços separados continuam abertos      |
| T-15        | pendente                                       | rastreabilidade final, riscos residuais, rollback e preparação do aceite humano                                           |

O painel operacional possui três lacunas de contrato explicitadas na spec. O backend atual só cria
revisão para ator existente; o botão de criação manual foi retirado até existir uma operação
transacional para ator, localização, contato e vínculo de rota. A API pública de rotas não fornece
estado editorial nem dimensões de prontidão, e o resumo de analytics não identifica pontos de
apoio. Por isso a interface não calcula mais percentuais com campos ausentes nem apresenta
completude cadastral como ranking de acesso. Novos pontos continuam entrando como rascunho pelo
CSV; prontidão e ranking permanecem indisponíveis até terem contratos administrativos auditáveis.

### B. Portões externos de homologação (`0H`)

- **0H-1 — privacidade e governança:** formalizar controlador, responsável por privacidade e canal
  do titular.
- **0H-2 — infraestrutura:** contratar e registrar hospedagem da API/frontend, tiles e mídia/CDN.
- **0H-3 — desempenho em campo:** validar LCP, INP e CLS em condições reais do piloto.
- **0H-4 — Google Places:** aprovar termos, credencial restrita, cotas, orçamento e atribuição antes
  de ativação externa.

## 3. Matriz de verificação

| Etapa | Descrição                                             | Estado   | Observação                                                    |
| ----- | ----------------------------------------------------- | -------- | ------------------------------------------------------------- |
| V1    | rastreabilidade e regressões por achado               | pendente | exige execução integrada e evidência final                    |
| V2    | autorização por papel, ação, objeto e região          | pendente | testes focados existem; falta validação integrada             |
| V3    | privacidade, throttling, RLS, retenção e concorrência | pendente | suíte Django passa; falta ensaio integrado de migrations/RLS |
| V4    | contratos e integração real web/admin/API             | pendente | contratos sincronizados; serviços separados ainda pendentes  |
| V5    | teclado, foco, tema, zoom e estados de erro           | pendente | interação manual/E2E ainda aberta                             |
| V6    | riscos residuais, rollback e decisão humana           | pendente | agentes não assinam GO                                        |

## 4. Evidências

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

**Estado atual:** **NO-GO — CORREÇÕES EM ANDAMENTO E VERIFICAÇÃO INTEGRADA PENDENTE**
_Revisado em 05/08/2026._
