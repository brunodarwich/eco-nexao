# Tasks — refinamento visual mobile e tema escuro

> Status: concluído  
> Atualizado em: 2026-07-29

## Dependências

- A execução pode ocorrer sem bloquear a tarefa 9 da spec `plataforma-mvp`.
- A navegação inferior depende de destinos públicos utilizáveis para Salvos e Perfil.
- Fotografias de produção dependem de aprovação editorial e direitos de uso.

## Plano executável

- [x] 1. Auditar visualmente os fluxos públicos em claro/escuro e nos viewports-alvo
  - Registrar capturas e medidas de altura do hero atual.
  - Verificar zoom de 200%, teclado, foco, contraste e áreas seguras.
  - _Requisitos: RF-DES-01, RF-DES-02, RF-DES-04, RNF-01_
  - Arquivos: `apps/web/src/app/styles.css`, `apps/web/src/components/route-experience.tsx`, `.kiro/specs/refinamento-visual-mobile/design.md`
  - Evidência: auditoria estrutural confirmou empilhamento dos três fatos, `gap` de 32 px no hero e soma de 48 px entre/pelas seções no breakpoint móvel.

- [x] 2. Evoluir os tokens semânticos do tema escuro em `packages/ui`
  - Introduzir superfícies `raised` e `interactive`, estados e divisores.
  - Validar contraste e equivalência do tema claro.
  - _Requisitos: RF-DES-01, RF-07, RNF-01_
  - Arquivos: `packages/ui/src/{styles.css,theme.ts}`, `.kiro/steering/design-system.md`
  - Evidência: fundo escuro `#090D09`, superfícies semânticas e `theme-color` sincronizados; tema claro recebeu equivalentes semânticos.

- [x] 3. Refatorar o hero da rota para composição mobile compacta
  - Criar app bar contextual, faixa de fatos e hierarquia de ações.
  - Preservar favorito, offline, atualização e alertas críticos.
  - _Requisitos: RF-DES-02, RF-DES-03, RF-03, RF-06_
  - Arquivos: `apps/web/src/components/{site-header.tsx,route-experience.tsx,route-local-actions.tsx}`, `apps/web/src/app/styles.css`, páginas da rota
  - Evidência: 390 × 844 com hero de 490 px, CTA e fatos na primeira tela; controles medidos com no mínimo 44 px.

- [x] 4. Reestruturar preparação e etapas para leitura escaneável
  - Separar preparação em grupos sem perder o conteúdo editorial atual.
  - Aproximar “Prepare-se para visitar” do resumo e criar linha do tempo compacta.
  - _Requisitos: RF-DES-02, RF-DES-04, RF-03_
  - Arquivos: `apps/web/src/components/route-experience.tsx`, `apps/web/src/app/styles.css`
  - Evidência: preparação inicia em 653 px no viewport 390 × 844; alertas completos seguem a preparação e alertas críticos mantêm resumo antes do CTA.

- [x] 5. Tornar as abas contextuais aderentes e revisar mapa/catálogo no tema escuro
  - Preservar URLs, alternativa textual do mapa e estado atual acessível.
  - Validar contraste de mapa, pins, filtros e bottom sheets.
  - _Requisitos: RF-DES-01, RF-DES-03, RF-04, RF-05_
  - Arquivos: `apps/web/src/{app/styles.css,components/route-experience.tsx}`, `apps/web/e2e/discovery.spec.ts`
  - Evidência: mapa e catálogo verificados em 430 × 932, sem overflow horizontal; abas mantêm `aria-current` e URLs compartilháveis.

- [x] 6. Avaliar navegação global inferior como entrega separada
  - Implementar somente quando Início, Rotas, Salvos e Perfil tiverem destinos completos.
  - Testar teclado virtual, `safe-area-inset-bottom` e conflito com CTAs.
  - _Requisitos: RF-DES-03_
  - Decisão: adiada até Salvos e Perfil terem destinos completos; Mapa e Catálogo permanecem contextuais à rota.

- [x] 7. Verificar e documentar evidências
  - Rodar testes unitários, E2E, acessibilidade e performance proporcionais ao risco.
  - Registrar arquivos, comandos, capturas e resultados antes de marcar tarefas concluídas.
  - _Requisitos: RF-DES-01 a RF-DES-04, RNF-01, RNF-02_
  - Verificação: Prettier; `pnpm --filter @econexao/web typecheck`; `test` (14 testes); `lint`; `build`; Playwright desktop e mobile (2 cenários).
  - Inspeção visual: 320 × 568, 390 × 844 e 430 × 932; sem overflow; controles de 44 px ou mais; tema escuro `#090D09`.

- [x] 8. Aplicar a linguagem visual à listagem pública de rotas
  - Compactar cabeçalho, introdução territorial e filtros no mobile.
  - Evoluir cards sem inventar fotografia ou conteúdo editorial.
  - Validar temas claro/escuro, nomes de região longos e ausência de overflow.
  - _Requisitos: RF-DES-01, RF-DES-03, RF-DES-04, RF-DES-05, RF-02_
  - Arquivos: `apps/web/src/{app/styles.css,components/routes-explorer.tsx}`, `apps/web/src/app/[regionSlug]/rotas/page.tsx`, `packages/ui/src/theme-toggle.tsx`, `apps/web/e2e/discovery.spec.ts`
  - Evidência: inspeção em 400 × 832 nos dois temas e 320 × 568; card inicia em 634 px no viewport de 400 px; filtros colapsam para uma coluna em 320 px; nenhum overflow horizontal; Playwright desktop e mobile aprovados.

## Ordem recomendada

`1 → 2 → 3 → 4 → 5 → 7`, com a tarefa 6 tratada como evolução posterior.
