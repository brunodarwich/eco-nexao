# Requirements — adequação visual responsiva à proposta

> Status: aprovado para implementação por solicitação direta do responsável  
> Responsável: produto e design  
> Atualizado em: 2026-07-31  
> Escopo: PWA pública em tela cheia, com shell de painel no desktop e composição móvel própria

## Contexto

As referências visuais abaixo apresentam uma linguagem de aplicativo móvel mais
fotográfica, imersiva e compacta do que a interface pública atual:

- `docs/design-proposals/econexao-dark-mobile-board-v1.png`
  (`1536 × 1024`, SHA-256
  `ADC6385AD12255F3832ED0B3698A33CF134DB062A03D43A8C053D2FE544FC006`);
- `docs/design-proposals/econexao-dark-route-pindobal-v1.png`
  (`863 × 1822`, SHA-256
  `9B3CD1BA97F6CC0020E055E53730240197123EB62FBAB9CA31D07299313C7F80`).

Os mockups são referências de composição e linguagem visual. Eles não autorizam a
publicação de fotografias, avaliações, atores, distâncias, preços ou pontos de interesse
sem origem editorial verificada. O segundo mockup é a referência principal para o
detalhe longo da rota; o quadro com três celulares define a coerência entre descoberta,
detalhe resumido e mapa.

O refinamento anterior, em `.kiro/specs/refinamento-visual-mobile`, já implantou tema
escuro, densidade móvel e abas contextuais. Esta spec cobre a diferença restante entre
a implementação atual e a nova proposta: mídia editorial real, hierarquia fotográfica,
iconografia consistente, navegação com aparência de aplicativo, mapa imersivo e
acabamento visual equivalente nos dois temas.

## Objetivo

Permitir que o Codex adeque a interface existente à proposta com critérios observáveis,
sem interpretar pixels do mockup como conteúdo factual e sem violar os princípios
multirregionais, editoriais, de privacidade e acessibilidade da ECOnexão.

## Escopo

### Incluído

- Tela móvel de descoberta/listagem de rotas.
- Tela móvel de detalhe da rota, incluindo hero, resumo, ações, preparação e etapas.
- Tela móvel do mapa, seus controles, resumo de etapas e alternativa textual.
- Contrato editorial de imagens de rota, etapa e ator, com texto alternativo e fallback.
- Tokens de tipografia, espaço, raio, borda, elevação, overlay e iconografia.
- Tema claro como padrão do produto e tema escuro equivalente à proposta.
- Estados de carregamento, ausência de imagem, erro, offline e conteúdo longo.
- App shell público de largura total, com linguagem de painel no desktop.
- Verificação responsiva de 320 px até monitores desktop amplos.

### Fora do escopo

- Conta obrigatória, rede social, avaliações públicas ou marketplace.
- Navegação curva a curva e rastreamento contínuo.
- Publicação automática de imagens ou textos por IA/importação.
- Uso de nomes, notas, estabelecimentos e fotografias ilustrativas do mockup como dados
  de produção.
- Criação imediata de `Salvos` e `Perfil` sem requisito funcional próprio.
- Reprodução da moldura do iPhone, barra de status do sistema ou Dynamic Island dentro
  da página web.

## Histórias e critérios de aceite

### RF-AV-01 — Linguagem visual coerente com a proposta

**História:** Como visitante, quero perceber a ECOnexão como um aplicativo de turismo
confiável, contemporâneo e ligado ao território.

1. QUANDO uma tela pública móvel for exibida O SISTEMA DEVE usar hierarquia baseada em
   fotografia editorial, superfícies discretas, texto de alto contraste e verde da marca
   concentrado em ações, estados e orientação.
2. QUANDO componentes equivalentes aparecerem em descoberta, detalhe, mapa ou catálogo
   O SISTEMA DEVE reutilizar tokens e padrões de forma, tipografia e iconografia.
3. QUANDO o tema claro estiver ativo O SISTEMA DEVE preservar a mesma hierarquia,
   densidade, semântica de cores e qualidade visual do tema escuro.
4. QUANDO a interface for exibida fora de um dispositivo iOS O SISTEMA NÃO DEVE
   simular elementos do sistema operacional que não pertençam à PWA.

### RF-AV-02 — Descoberta fotográfica e compacta

**História:** Como visitante, quero comparar rotas por imagem, nome, local, duração e
dificuldade sem atravessar formulários extensos.

1. QUANDO a região tiver rotas publicadas O SISTEMA DEVE mostrar saudação curta, título
   de exploração, região ativa, busca e cards de destaque em ordem editorial.
2. QUANDO uma rota tiver imagem de capa publicada O SISTEMA DEVE usar a imagem como
   fundo do card, com overlay que preserve a leitura do texto.
3. SE uma rota não tiver imagem publicada ENTÃO O SISTEMA DEVE usar fallback editorial
   neutro baseado em tokens, sem gerar ou inferir uma paisagem.
4. QUANDO duração e dificuldade estiverem disponíveis O SISTEMA DEVE mostrá-las em
   chips compactos com ícone e texto.
5. QUANDO o visitante ativar filtros avançados O SISTEMA DEVE manter a busca como
   controle primário e revelar os demais filtros sem deslocamento excessivo.

### RF-AV-03 — Detalhe imersivo e informativo

**História:** Como visitante, quero entender a promessa, o esforço, o custo e a
preparação da rota antes de iniciá-la.

1. QUANDO a rota tiver imagem hero publicada O SISTEMA DEVE posicioná-la após a app bar
   e aplicar transição gradual para a superfície de conteúdo.
2. QUANDO a rota não tiver imagem hero O SISTEMA DEVE preservar título, promessa,
   fatos, CTA e ordem de leitura sem espaço vazio reservado.
3. QUANDO duração, dificuldade e custo forem exibidos O SISTEMA DEVE agrupá-los em uma
   faixa compacta de uma linha, permitindo reflow acessível em telas estreitas.
4. QUANDO o usuário visualizar o detalhe O SISTEMA DEVE encontrar `Iniciar rota`,
   `Salvar offline` e `Favoritar` antes das seções extensas.
5. SE houver alerta crítico ativo ENTÃO O SISTEMA DEVE apresentá-lo antes de `Iniciar
   rota`; alertas não críticos podem aparecer na preparação.
6. QUANDO `Iniciar rota` for acionado O SISTEMA DEVE abrir o mapa contextual da rota,
   sem prometer navegação curva a curva.

### RF-AV-04 — Preparação e etapas escaneáveis

**História:** Como visitante, quero reconhecer rapidamente como chegar, o que levar,
qual o melhor horário e quais são as etapas.

1. QUANDO houver conteúdo de preparação O SISTEMA DEVE organizá-lo em linhas com ícone,
   título, resumo e affordance de expansão ou navegação.
2. QUANDO uma informação não estiver publicada O SISTEMA NÃO DEVE exibir linha vazia,
   texto fictício ou ícone sem rótulo.
3. QUANDO houver alertas de atenção O SISTEMA DEVE usar amarelo em superfície contida,
   ícone e texto; a cor não pode ser o único sinal.
4. QUANDO etapas forem exibidas O SISTEMA DEVE manter ordem, duração, descrição,
   opcionalidade e relação visual de sequência.
5. SE uma etapa tiver miniatura editorial publicada ENTÃO O SISTEMA DEVE mostrá-la sem
   substituir nome, duração ou descrição textual.

### RF-AV-05 — Mapa imersivo com alternativa acessível

**História:** Como visitante, quero ver o percurso e as próximas etapas sem perder uma
alternativa textual completa.

1. QUANDO a aba `Mapa` abrir no celular O SISTEMA DEVE priorizar o mapa em tela ampla,
   com app bar sobreposta, controles de camada e centralização acessíveis.
2. QUANDO rota, etapas e atores forem desenhados O SISTEMA DEVE diferenciar categorias
   por forma, ícone e texto, não apenas por cor.
3. QUANDO o resumo inferior estiver recolhido O SISTEMA DEVE mostrar uma alça, título,
   quantidade de etapas visíveis e ação para ver todas.
4. QUANDO o resumo inferior for expandido O SISTEMA DEVE manter foco, leitura,
   rolagem, botão voltar e área segura previsíveis.
5. QUANDO o mapa falhar, estiver offline ou for ignorado por tecnologia assistiva O
   SISTEMA DEVE fornecer a lista textual de etapas e ações equivalentes.
6. QUANDO a localização for solicitada O SISTEMA DEVE explicar o uso antes da permissão,
   mantê-la opcional e processá-la somente no dispositivo.

### RF-AV-06 — Mídia editorial rastreável

**História:** Como equipe editorial, quero associar imagens verificadas a rotas, etapas
e atores sem quebrar a experiência quando não houver mídia.

1. QUANDO uma imagem for publicada O SISTEMA DEVE conhecer arquivo/URL, proporção ou
   dimensões, texto alternativo, crédito, origem, licença, estado editorial e ponto focal.
2. QUANDO uma importação CSV, automação ou IA sugerir uma imagem O SISTEMA DEVE
   mantê-la como rascunho até aprovação humana.
3. SE uma imagem for removida, expirar ou falhar ENTÃO O SISTEMA DEVE voltar ao fallback
   sem remover informação textual ou ação essencial.
4. QUANDO a imagem for meramente decorativa O SISTEMA DEVE permitir texto alternativo
   vazio; quando trouxer informação adicional, o texto alternativo deve ser descritivo.
5. QUANDO a mídia for entregue ao frontend O SISTEMA DEVE fornecer variantes
   responsivas e evitar expor metadados pessoais desnecessários.

### RF-AV-07 — Navegação móvel real, não cenográfica

**História:** Como visitante, quero navegação persistente apenas para destinos que
existam e sejam utilizáveis.

1. QUANDO a navegação inferior for implementada O SISTEMA DEVE usar somente destinos
   públicos reais, com estado atual, rótulo textual e alvo de toque adequado.
2. SE `Salvos` ou `Perfil` não tiverem requisitos e páginas aprovados ENTÃO O SISTEMA
   NÃO DEVE publicar itens inertes ou telas cenográficas.
3. QUANDO `Mapa` e `Catálogo` forem exibidos O SISTEMA DEVE mantê-los como abas
   contextuais da rota.
4. QUANDO a barra inferior coexistir com CTA, teclado ou bottom sheet O SISTEMA DEVE
   respeitar `safe-area-inset-bottom` e impedir sobreposição de conteúdo.

### RF-AV-08 — Conteúdo multirregional e editorial

**História:** Como visitante de qualquer território publicado, quero que a composição
funcione sem depender dos nomes ilustrados nos mockups.

1. QUANDO a interface for renderizada O SISTEMA DEVE obter região, rota, etapas, atores
   e alertas do domínio publicado, sem strings territoriais fixas no componente.
2. QUANDO nomes longos ocuparem duas ou três linhas O SISTEMA DEVE refluir sem truncar
   informação essencial.
3. QUANDO conteúdo externo for descoberto O SISTEMA DEVE manter revisão humana antes da
   publicação.

### RF-AV-09 — App shell de tela cheia no desktop

**História:** Como visitante em um computador, quero usar toda a área disponível em uma
interface com organização de painel, para explorar mais conteúdo sem vê-lo comprimido em
uma coluna central estreita.

1. QUANDO a viewport tiver largura de desktop O SISTEMA DEVE ocupar toda a largura e a
   altura útil da janela com um app shell composto por navegação, barra superior e área
   principal fluida.
2. QUANDO o conteúdo principal for renderizado no desktop O SISTEMA NÃO DEVE aplicar um
   `max-width` global que deixe grandes margens vazias nas laterais.
3. QUANDO a largura disponível aumentar O SISTEMA DEVE redistribuir cards, mapa, filtros
   e painéis contextuais em colunas, sem esticar parágrafos para linhas excessivamente
   longas.
4. QUANDO a navegação lateral existir O SISTEMA DEVE mostrar apenas destinos públicos,
   indicar o destino atual e permitir operação por teclado.
5. QUANDO o produto adotar aparência de painel O SISTEMA NÃO DEVE expor ações
   administrativas, estado editorial ou controles protegidos ao visitante público.
6. QUANDO a viewport ficar abaixo do breakpoint de desktop O SISTEMA DEVE trocar a
   composição estrutural, e não apenas encolher a sidebar ou os cards.

## Requisitos não funcionais

### RNF-AV-01 — Acessibilidade WCAG 2.2 AA

- Texto normal deve atingir contraste mínimo de `4.5:1`; texto grande, `3:1`;
  componentes e foco, `3:1` contra cores adjacentes.
- Alvos de toque devem medir no mínimo `44 × 44 CSS px`.
- A ordem DOM deve permanecer significativa com CSS, imagens ou mapa indisponíveis.
- Zoom de 200%, contraste forçado, leitor de tela, teclado e movimento reduzido devem
  preservar todas as ações essenciais.

### RNF-AV-02 — Desempenho móvel

- Hero e capas devem reservar dimensões para evitar CLS.
- A imagem LCP do detalhe pode ser priorizada; miniaturas fora da dobra devem ser lazy.
- Formatos modernos, `srcset`/`sizes` e orçamento de bytes devem ser definidos antes da
  implantação.
- Ícones devem ser SVGs locais ou biblioteca aprovada, nunca fonte de ícones ou emoji.

### RNF-AV-03 — Responsividade

- A composição deve ser verificada em `320 × 568`, `390 × 844`, `430 × 932`, tablet e
  desktop nas larguras de `1280`, `1440`, `1920` e `2560 px`.
- Nenhum viewport deve apresentar rolagem horizontal não intencional.
- O conteúdo deve respeitar áreas seguras sem codificar dimensões de um aparelho.
- Áreas de leitura contínua devem permanecer entre aproximadamente `60` e `80ch`, mesmo
  quando o shell ocupar a tela inteira.

### RNF-AV-04 — Testabilidade visual

- Componentes críticos devem possuir estados reproduzíveis em fixtures.
- Capturas de referência devem cobrir tema claro/escuro, com/sem imagem, conteúdo curto/
  longo, mapa disponível/indisponível e alertas.
- Diferenças visuais devem usar tolerância documentada e não substituir testes de
  acessibilidade ou comportamento.

## Regras de negócio

### RB-AV-01 — Mockup não é fonte editorial

- Fotografias, nomes de atores, avaliações, distâncias e pontos presentes nas imagens
  são ilustrativos até validação e publicação humana.

### RB-AV-02 — Tema claro continua padrão

- A proposta escura orienta o tema dark; no primeiro acesso, sem escolha persistida, o
  produto inicia em tema claro. Uma escolha explícita por claro ou escuro prevalece e
  permanece persistida localmente.

### RB-AV-03 — Sem conta obrigatória

- Descoberta, detalhe, mapa e catálogo continuam públicos. Favoritar e offline devem
  funcionar localmente no MVP quando não houver conta.

### RB-AV-04 — Sem rastreamento

- `Iniciar rota` abre orientação contextual; não transforma a aplicação em serviço de
  rastreamento ou navegação curva a curva.

## Casos de borda e falhas

- Capa ausente, vertical, de baixa resolução, com ponto focal extremo ou falha de rede.
- Região e rota com nomes longos; promessa com até três linhas.
- Custo ausente ou `Consulte localmente`.
- Uma única rota publicada ou dezenas de rotas.
- Etapa sem miniatura, duração ou descrição.
- Alerta crítico longo e múltiplos alertas simultâneos.
- Mapa sem tiles, sem WebGL, offline ou com permissão de localização negada.
- Bottom sheet com teclado virtual e zoom de 200%.
- Modo standalone, navegador móvel e desktop.
- Desktop ultrawide, janela redimensionada e sidebar expandida/recolhida.
- Tema claro, escuro, contraste forçado e preferência por movimento reduzido.

## Decisões de aprovação

- [x] Aprovar esta spec como sucessora visual da spec concluída
  `refinamento-visual-mobile`.
- [ ] Definir política e origem das fotografias de produção.
- [ ] Decidir se a navegação inferior entra somente após specs próprias de `Salvos` e
  `Perfil`, ou se a primeira versão terá apenas destinos já existentes.
- [ ] Validar o conjunto final de ícones e licenciamento.
