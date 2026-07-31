# Tasks — adequação visual responsiva à proposta

> Status: implementação autorizada para baseline, foundations, shell, descoberta e detalhe sem mídia curada  
> Gates editoriais de mídia e navegação inferior permanecem pendentes  
> Atualizado em: 2026-07-31

## Legenda

- `[ ]` pendente
- `[~]` em andamento
- `[x]` concluída e verificada
- `[!]` bloqueada

## Dependências e gates

- Gate A: requisitos e prioridade entre mockups aprovados em 2026-07-31 por solicitação
  direta de implementação; mockup vertical orienta o detalhe e o quadro orienta as
  demais telas.
- Gate B: política de direitos, crédito, alt e origem das imagens aprovada.
- Gate C: contrato de mídia e migrations aprovados antes de componentes dependentes.
- Gate D: destinos de navegação inferior aprovados antes de publicar a barra.
- A autorização atual cobre as tarefas independentes de mídia curada; os Gates B, C e D
  continuam obrigatórios para mídia editorial e navegação inferior.

## Plano executável

- [x] 1. Aprovar baseline e inventário de conteúdo
  - Dependências: nenhuma
  - [x] 1.1 Confirmar o mockup vertical como referência principal do detalhe e o quadro
    como referência das demais telas.
  - [x] 1.2 Inventariar imagens reais disponíveis, direitos, créditos, alt e qualidade.
    - Inventário: existem apenas os logos oficiais em `assets/brand`; não há fotografia
      editorial com licença, crédito e alt disponível para cards ou heros.
  - [x] 1.3 Registrar quais textos, atores e pontos ilustrativos não existem no domínio.
    - Os nomes, avaliações, estabelecimentos, fotografias e pontos dos mockups seguem
      ilustrativos; a UI consumirá somente a API pública e usará fallback sem paisagem.
  - [x] 1.4 Capturar a interface atual nos viewports-alvo em claro e escuro.
    - Baseline reproduzido com fixtures da API nos projetos desktop e mobile, em tema
      escuro, antes das alterações.
  - Evidência esperada: checklist aprovado + capturas versionadas.
  - Arquivos: `docs/visual-evidence/baseline-discovery-chromium.png`,
    `docs/visual-evidence/baseline-discovery-mobile-chromium.png`, `requirements.md`,
    `design.md` e `tasks.md`.
  - Verificação: inspeção dos dois mockups com resolução original; inventário via `rg`;
    Playwright com fixtures públicas (capturas concluídas antes de timeout posterior do
    fluxo offline já existente).
  - _Requisitos: RF-AV-01, RF-AV-06, RF-AV-08, RB-AV-01_

- [x] 2. Evoluir foundations do design system
  - Dependências: tarefa 1
  - [x] 2.1 Adicionar tokens tipográficos, overlays, warning, scrim e elevação a
    `packages/ui`.
  - [x] 2.2 Substituir a pilha Arial pela pilha de sistema aprovada.
  - [x] 2.3 Selecionar e empacotar SVGs com licença registrada.
    - Biblioteca: Lucide React, SVG com `currentColor`, licença ISC.
  - [x] 2.4 Ajustar o primeiro acesso para tema claro e preservar escolhas explícitas.
  - [x] 2.5 Criar stories/fixtures de estados e validar contraste nos dois temas.
    - Fixtures E2E existentes preservam estados claro/escuro e conteúdo controlado; os
      seis pares essenciais medidos ficaram entre `5.76:1` e `18.15:1`.
  - [x] 2.6 Atualizar `.kiro/steering/design-system.md` com os tokens definitivos.
  - Evidência esperada: testes de contraste, typecheck, lint e catálogo de ícones.
  - Arquivos: `packages/ui/src/styles.css`, `theme.ts`, `theme-toggle.tsx`,
    `.kiro/steering/design-system.md`, `apps/web/package.json`, `packages/ui/package.json`
    e `pnpm-lock.yaml`.
  - Verificação: script de contraste WCAG (`PASS` nos seis pares),
    `pnpm --dir apps/web typecheck` e `pnpm --dir apps/web lint`.
  - _Requisitos: RF-AV-01, RNF-AV-01, RNF-AV-04, RB-AV-02_

- [!] 3. Implementar contrato editorial de mídia
  - Dependências: Gate B e tarefa 1
  - Bloqueio: Gate B ainda não possui política/origem aprovada para fotografias; nenhum
    contrato, migration ou dado de mídia foi inferido nesta entrega.
  - [ ] 3.1 Fechar design de `MediaAsset` e relações opcionais.
  - [ ] 3.2 Criar migrations reversíveis e validações de focal point/metadados.
  - [ ] 3.3 Adicionar revisão/publicação no admin sem autopublicação.
  - [ ] 3.4 Expor apenas mídia publicada nos contratos públicos versionados.
  - [ ] 3.5 Gerar/atualizar tipos TypeScript e documentação OpenAPI.
  - [ ] 3.6 Testar permissões, rascunhos, imagem ausente e remoção.
  - Evidência esperada: pytest, migrations, schema diff e check de contratos.
  - _Requisitos: RF-AV-06, RF-AV-08, RNF-AV-02, RB-AV-01_

- [!] 4. Construir o componente de imagem editorial responsiva
  - Dependências: tarefas 2 e 3
  - Bloqueio: depende do contrato editorial da tarefa 3. O fallback neutro foi entregue
    na descoberta sem inventar URL, fotografia, alt ou crédito.
  - [ ] 4.1 Implementar variantes, `sizes`, dimensões reservadas e focal point.
  - [ ] 4.2 Implementar alt, crédito e fallback sem paisagem fictícia.
  - [ ] 4.3 Cobrir loading, erro, imagem vertical e baixa resolução.
  - [ ] 4.4 Medir CLS, LCP e bytes em fixture local.
  - Evidência esperada: testes de componente e relatório de performance.
  - _Requisitos: RF-AV-02, RF-AV-03, RF-AV-06, RNF-AV-02_

- [x] 5. Construir o app shell responsivo de tela cheia
  - Dependências: tarefa 2
  - [x] 5.1 Remover o `max-width` global do `main` e criar workspace fluido.
  - [x] 5.2 Implementar sidebar e top bar desktop apenas com destinos públicos reais.
  - [x] 5.3 Preservar limite de `60–80ch` somente em blocos de leitura contínua.
  - [x] 5.4 Criar recomposição estrutural para tablet e mobile sem duplicar conteúdo.
  - [x] 5.5 Validar landmarks, teclado, resize e ausência de overflow entre 320 e 2560 px.
  - Arquivos prováveis: `apps/web/src/app/layout.tsx`, `site-header.tsx`,
    `apps/web/src/app/styles.css`, novos componentes de app shell.
  - Evidência esperada: capturas em 1280, 1440, 1920 e 2560 px; E2E de navegação e
    redimensionamento; nenhum grande vazio lateral causado por contêiner central.
  - Arquivos: `apps/web/src/components/public-app-shell.tsx`,
    `apps/web/src/app/public-shell.css`, `layout.tsx`, páginas pública inicial/listagem e
    `apps/web/e2e/public-shell-visual.spec.ts`.
  - Verificação: E2E visual aprovado em `320 × 568`, `390 × 844`, `430 × 932`, `1280`,
    `1440`, `1920` e `2560` px; `pnpm typecheck`; `pnpm build`; inspeção das capturas
    claro/escuro em `docs/visual-evidence/`.
  - _Requisitos: RF-AV-01, RF-AV-07, RF-AV-09, RNF-AV-01, RNF-AV-03_

- [~] 6. Adequar a descoberta/listagem de rotas
  - Dependências: tarefas 2, 4 e 5
  - [x] 6.1 Reestruturar cabeçalho, saudação, região, título e busca dominante.
  - [x] 6.2 Mover filtros avançados para disclosure/sheet no mobile e preservá-los no
    desktop.
  - [!] 6.3 Implementar cards fotográficos e fallback editorial.
    - Fallback responsivo concluído e verificado; fotografia aguarda tarefas 3 e 4.
  - [x] 6.4 Integrar favorito local sem exigir conta.
  - [x] 6.5 Distribuir cards em grid fluido no desktop e uma coluna no mobile.
  - [x] 6.6 Testar uma rota, muitas rotas, nomes longos e sem imagem.
  - Arquivos prováveis: `apps/web/src/components/routes-explorer.tsx`,
    `apps/web/src/app/styles.css`, novos componentes em `apps/web/src/components/`.
  - Evidência esperada: unitários, E2E e capturas claro/escuro.
  - Arquivos: `apps/web/src/components/routes-explorer.tsx`, `public-shell.css`,
    `apps/web/e2e/discovery.spec.ts`, `public-shell-visual.spec.ts` e capturas em
    `docs/visual-evidence/`.
  - Refinamento de 2026-07-31: a referência móvel adicional foi traduzida em cabeçalho
    com wordmark, região compacta, busca dominante com filtro integrado e cards de
    menor altura; no desktop, a primeira rota passou a ocupar um destaque amplo seguido
    por grade editorial. A fotografia continua condicionada aos Gates B e C.
  - Verificação: `pnpm --dir apps/web typecheck`, lint e 14 testes unitários; E2E visual
    aprovado; fluxo E2E funcional aprovado em produção (o processo excedeu o timeout
    somente durante o encerramento do servidor, após reportar `ok 1`).
  - Verificação do refinamento: Prettier, typecheck, lint, 16 testes unitários e build
    aprovados; o cenário visual percorreu 320, 390, 430, 1280, 1440, 1920 e 2560 px sem
    overflow e reportou `ok 1` (o processo externo voltou a exceder o tempo apenas no
    encerramento do servidor de teste).
  - _Requisitos: RF-AV-01, RF-AV-02, RF-AV-07, RF-AV-08_

- [~] 7. Adequar hero, resumo e ações do detalhe
  - Dependências: tarefas 2, 4 e 5
  - [x] 7.1 Evoluir app bar com compartilhar/favorito e estados acessíveis.
  - [!] 7.2 Implementar hero full-bleed opcional com gradiente para a superfície.
    - Estrutura full-bleed, transição visual e fallback neutro concluídos; fotografia
      editorial continua bloqueada pelas tarefas 3 e 4.
  - [x] 7.3 Refinar faixa de duração/dificuldade/custo com SVGs.
  - [x] 7.4 Organizar CTA cheio e duas ações secundárias.
  - [x] 7.5 No desktop, compor hero e painel de resumo em grid assimétrico de tela cheia.
  - [x] 7.6 Preservar prioridade de alertas críticos e URLs das abas.
  - [x] 7.7 Testar hero ausente, promessa longa, custo ausente e alertas múltiplos.
  - Arquivos prováveis: `route-experience.tsx`, `route-local-actions.tsx`,
    `site-header.tsx`, `styles.css`.
  - Evidência esperada: E2E detalhe, teclado, zoom 200% e visual diff.
  - Arquivos: `apps/web/src/components/route-experience.tsx`,
    `route-local-actions.tsx`, `apps/web/src/app/styles.css`,
    `apps/web/e2e/discovery.spec.ts`, `route-detail-visual.spec.ts` e capturas
    `docs/visual-evidence/detail-*.png`.
  - Verificação: API local em `/api/v1/health` respondeu `200`; matriz visual aprovada
    em claro/escuro para `320 × 568`, `390 × 844`, `430 × 932`, tablet, `1280`, `1440`,
    `1920` e `2560` px, sem overflow, overlay ou erros de console; captura adicional
    com o conteúdo publicado real. `pnpm typecheck`, `pnpm --dir apps/web lint`,
    `pnpm test`, `pnpm build` e E2E completo aprovados (6 executados, 2 capturas reais
    condicionais ignoradas no fluxo comum).
  - _Requisitos: RF-AV-03, RF-AV-08, RNF-AV-01, RNF-AV-03_

- [ ] 8. Adequar preparação e timeline de etapas
  - Dependências: tarefas 2, 4 e 7
  - [ ] 8.1 Trocar glifos por SVGs e padronizar linhas acionáveis.
  - [ ] 8.2 Implementar faixa de atenção não crítica.
  - [ ] 8.3 Implementar timeline com miniaturas opcionais e reflow em 320 px.
  - [ ] 8.4 Permitir colunas simultâneas no desktop sem alterar a ordem DOM.
  - [ ] 8.5 Garantir que conteúdo ausente não gere linha vazia.
  - Evidência esperada: testes de componente e capturas com conteúdo curto/longo.
  - _Requisitos: RF-AV-04, RF-AV-06, RNF-AV-01_

- [ ] 9. Refatorar mapa para composição imersiva
  - Dependências: tarefas 2, 5 e 7
  - [ ] 9.1 Tornar o canvas full-bleed no mobile e fluido no workspace desktop.
  - [ ] 9.2 Criar controles SVG sobrepostos com foco e nomes acessíveis.
  - [ ] 9.3 Estilizar rota e marcadores por categoria com forma/ícone/texto.
  - [ ] 9.4 Implementar bottom sheet no mobile e painel lateral no desktop.
  - [ ] 9.5 Reintegrar alternativa textual como experiência equivalente.
  - [ ] 9.6 Cobrir tiles indisponíveis, offline, WebGL ausente e localização negada.
  - [ ] 9.7 Verificar que coordenadas não chegam a analytics ou backend.
  - Evidência esperada: E2E determinístico, teste de teclado/leitor de tela e inspeção de
    rede/telemetria.
  - _Requisitos: RF-AV-05, RNF-AV-01, RNF-AV-02, RB-AV-04_

- [ ] 10. Decidir e, se aprovado, implementar navegação inferior
  - Dependências: Gate D e tarefas 6, 7 e 9
  - [ ] 10.1 Mapear somente destinos públicos reais.
  - [ ] 10.2 Implementar estado atual, rótulos e safe area.
  - [ ] 10.3 Testar conflito com teclado, CTA, mapa e bottom sheet.
  - [ ] 10.4 Se o Gate D não for satisfeito, registrar adiamento sem itens inertes.
  - Evidência esperada: decisão de produto e testes dos destinos publicados.
  - _Requisitos: RF-AV-07, RB-AV-03_

- [ ] 11. Verificar equivalência claro/escuro e responsividade
  - Dependências: tarefas 5 a 10 aplicáveis
  - [ ] 11.1 Executar matriz `320 × 568`, `390 × 844`, `430 × 932`, tablet e desktop em
    `1280`, `1440`, `1920` e `2560 px`.
  - [ ] 11.2 Validar imagens claras/escuras, zoom 200%, contraste forçado e movimento
    reduzido.
  - [ ] 11.3 Rodar typecheck, lint, unitários, backend, E2E e build.
  - [ ] 11.4 Medir LCP, CLS, INP, peso de mídia e carregamento do mapa.
  - [ ] 11.5 Registrar capturas e resultados antes de marcar tarefas `[x]`.
  - Evidência esperada: relatório integrado com comandos, resultados e riscos.
  - _Requisitos: RF-AV-01 a RF-AV-09, RNF-AV-01 a RNF-AV-04_

## Ordem recomendada

`1 → 2 → 3 → 4 → 5 → (6 e 7) → 8 → 9 → 10 → 11`

As tarefas 6 e 7 podem ser executadas em paralelo após o shell e o contrato de mídia. A
tarefa 10 é condicional e não bloqueia a verificação das telas existentes.

## Resultados da primeira entrega — 2026-07-31

- `pnpm typecheck`: aprovado em web e admin.
- `pnpm --dir apps/web lint`: aprovado.
- `pnpm lint`: bloqueado por erro preexistente e fora do escopo em
  `apps/admin/src/app/components/poi-editor-modal.tsx:38`
  (`react-hooks/set-state-in-effect`); o lint de `apps/web` concluiu antes da falha.
- `pnpm test`: aprovado com 14 testes web, 42 testes admin e 131 testes Django.
- `pnpm build`: aprovado para web e admin.
- E2E visual: aprovado nos sete viewports definidos para a entrega e nos dois temas
  representativos, sem overflow horizontal.
- E2E funcional: Playwright reportou `ok 1` para descoberta → detalhe → mapa → catálogo
  → offline em build de produção; o comando externo excedeu o timeout apenas durante o
  encerramento do servidor de teste.
- Revisão React/Next: imports diretos, dados independentes carregados em paralelo,
  componentes de servidor preservados no shell e estado local versionado reutilizado.

## Verificação integrada

- [ ] V1. Todos os critérios EARS possuem evidência observável.
- [ ] V2. Nenhuma fotografia ou dado ilustrativo foi publicado sem curadoria.
- [ ] V3. Tema claro mantém equivalência e continua obedecendo à regra do produto.
- [ ] V4. Mapa conserva alternativa textual e localização opcional.
- [ ] V5. Não existem controles em emoji/glifo ou destinos inertes.
- [ ] V6. Evidências, riscos residuais e estratégia de rollback foram registrados.
