# Relatório de Go/No-Go do Piloto, Riscos Residenciais e Evidências — V5 (Congelamento & Contenção)

**Projeto:** Plataforma ECOnexão (MVP Multirregional — Piloto Pindobal/Santarém-Alter do Chão)  
**Data da Avaliação:** 31 de Julho de 2026  
**Responsável por Produto e Tecnologia:** Bruno (interino)  
**Decisão Integrada de Go/No-Go:** **NO-GO (CONGELADO DEVIDO A ACHADOS P0/P1 E PORTÕES 0H ABERTOS)**

---

## 1. Resumo Executivo e Separação por Ambiente

A revisão pós-implementação identificou achados críticos de segurança, integridade transacional, privacidade, roteamento frontend/API, acessibilidade e governança. Conforme as regras de governança do projeto (`AGENTS.md` e `revisao-pos-mvp`), a declaração anterior de GO foi revertida e congelada em **NO-GO**.

### Status da Avaliação por Ambiente:

1. **Ambiente Local de Desenvolvimento:**
   - **Status:** Permitido exclusivamente para execução de suítes de teste e correções orientadas por especificação.
2. **Ambiente de Homologação / Staging:**
   - **Status:** **NO-GO**. Bloqueado até a conclusão verificada de todas as tarefas de `revisao-pos-mvp` (1 a 15) e encerramento formal dos portões `0H`.
3. **Lançamento Público Aberto com Tráfego Real:**
   - **Status:** **NO-GO**. Estritamente vedado qualquer tráfego público até resolução dos bloqueadores técnicos e aceite humano explícito.

---

## 2. Bloqueadores Abertos (Spec `revisao-pos-mvp`) e Portões `0H`

### A. Bloqueadores Técnicos (Tarefas 1 a 15 - Spec `revisao-pos-mvp`)
- **T-01:** Moderação e auditoria não atômicas (risco de 500 com alteração persistida e sem auditoria).
- **T-02:** Autorização regional e de escopo administrativo ausente/incompleta em endpoints protegidos.
- **T-03:** Ingestão de analytics sem allowlist estrita e sem proteção contra PII, coordenadas e concorrência.
- **T-04:** Ausência de rate limiting / throttling (`429`) em endpoints públicos de relatos e analytics.
- **T-05:** Tabelas novas sem RLS (`relrowsecurity=true`) e ausência de expurgo de retenção atômico.
- **T-06:** Relatos sem validação de alvo no domínio publicado e com mutabilidade indevida de conteúdo original.
- **T-07:** Roteamento frontend/API descentralizado e falha de proxy entre Web, Admin e API em processos separados.
- **T-08:** Divergência de OpenAPI/contratos TypeScript com respostas reais da API.
- **T-09:** Editor administrativo simulando publicação local sem passar pelo workflow persistente auditado.
- **T-10:** Comando de seed multirregional não atômico/idempotente com risco de rebaixamento de versão.
- **T-11:** Revogação de consentimento de analytics sem interrupção imediata e expurgo de fila local.
- **T-12:** Violições de WCAG 2.2 AA em diálogos (foco/Escape) e abas (navegação por setas/roving tabIndex).
- **T-13:** Respeito incorreto a `prefers-color-scheme` e ausência de estados de erro diferenciados (401/403/429/500).
- **T-14 & T-15:** Verificação integrada e validação de contratos pendentes.

### B. Portões de Homologação Externos (`0H`)
- **0H-1 (Privacidade & Governança):** Designação formal do Encarregado de Dados (DPO/LGPD), definição do controlador e canal do titular.
- **0H-2 (Infraestrutura & Hospedagem):** Contratação e configuração de provedores de hospedagem da API/Frontend, banco gerenciado, tiles e CDN de mídia.
- **0H-3 (Desempenho em Campo):** Validação dos orçamentos de desempenho (LCP <= 2.5s, INP <= 200ms, CLS <= 0.1 p75) em redes 3G/4G no piloto de Pindobal.
- **0H-4 (Google Places API):** Chave restrita por IP/Referer, cotas, alertas de orçamento, termos, atribuição e aprovação prévia para ativação externa.

---

## 3. Matriz de Evidências das Etapas de Verificação

| Etapa | Descrição | Status | Evidências e Observações |
| :--- | :--- | :--- | :--- |
| **V1** | Matriz de rastreabilidade e validação de contratos | **Pendente `[ ]`** | Aguardando revalidação `pnpm contracts:check` pós-correções da spec. |
| **V2** | Testes E2E, acessibilidade manual e navegação mobile | **Pendente `[ ]`** | Aguardando execução do Playwright em processos separados. |
| **V3** | Backup, RLS, retenção, rollback de aplicação e conteúdo | **Pendente `[ ]`** | Aguardando validação de RLS e migrações atômicas. |
| **V4** | Registro de evidências, riscos residuais e decisão de go/no-go | **Pendente `[ ]`** | Decisão mantida formalmente em **NO-GO**. |

---

## 4. Evidências da Linha de Base (Fase 0)

- **Comando `pnpm check`:**
  - `contracts:check`: Sucesso (OpenAPI e TypeScript sincronizados).
  - `lint`: Sucesso (`apps/web`, `apps/admin`, e `ruff check` na API Django).
  - `format:check`: Sucesso (145 arquivos formatados via Prettier e ruff).
  - `typecheck`: Sucesso (`apps/web`, `apps/admin`).
  - `test`: Sucesso (Web: 4/4 arquivos, 21 testes; Admin: 9/9 arquivos, 41 testes; API Django: 173 testes aprovados em 8.41s).
  - `build`: Sucesso (Build de produção Next.js das duas aplicações `apps/web` e `apps/admin`).
- **Comando `pnpm test:e2e`:**
  - Execução no Playwright: 8 cenários aprovados, 2 ignorados (descoberta e layout responsivo em `chromium` e `mobile-chromium`). Tempo total 59.5s.

---

## 5. Governança e Declaração de Aceite

> **IMPORTANTE:** Agentes e sistemas automatizados NÃO possuem autoridade para assinar o aceite humano ou converter a decisão para GO. A aprovação de homologação e produção é exclusiva do responsável humano.

**Estado Atual:** **NO-GO (SUBMETIDO PARA REVISÃO E CORREÇÃO)**  
*Revisado em 31/07/2026.*
