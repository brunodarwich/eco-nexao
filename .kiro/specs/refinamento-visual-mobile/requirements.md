# Requirements — refinamento visual mobile e tema escuro

> Status: aprovado e implementado  
> Atualizado em: 2026-07-29  
> Escopo: PWA pública, com prioridade para a rota de Pindobal no celular

## Contexto

A interface atual atende à fundação funcional, porém o detalhe da rota ocupa altura
excessiva no celular antes de apresentar conteúdo de preparação. O tema escuro também
precisa de uma hierarquia mais profunda: fundo quase preto, superfícies discretas e cores
da marca concentradas em ações, seleção, status e orientação.

## Histórias e critérios de aceite

### RF-DES-01 — Tema escuro de alto contraste

**História:** Como visitante, quero uma interface escura confortável e claramente
hierarquizada para usar o aplicativo em diferentes condições de luz.

1. QUANDO o tema escuro estiver ativo O SISTEMA DEVE usar fundo preto ou cinza quase
   preto e superfícies visualmente distintas sem depender de sombras fortes.
2. QUANDO uma ação, aba ou estado receber destaque O SISTEMA DEVE usar as cores da
   marca com parcimônia e contraste WCAG 2.2 AA.
3. QUANDO conteúdo comum for apresentado O SISTEMA NÃO DEVE usar verde ou amarelo
   como cor dominante da superfície.
4. QUANDO o mapa estiver no tema escuro O SISTEMA DEVE manter rota, pins, controles e
   alternativa textual legíveis.

### RF-DES-02 — Densidade do detalhe da rota no celular

**História:** Como visitante, quero entender a rota e encontrar a preparação rapidamente,
sem atravessar grandes áreas vazias ou blocos repetitivos.

1. QUANDO a rota abrir em viewport de 320 a 480 px O SISTEMA DEVE exibir título,
   promessa, resumo, ação principal e abas com espaçamento compacto.
2. QUANDO duração, dificuldade e custo forem exibidos no celular O SISTEMA DEVE
   agrupá-los em uma linha ou grade compacta, sem três cards verticais isolados.
3. QUANDO não houver alerta crítico O SISTEMA DEVE tornar o início de “Prepare-se para
   visitar” visível na primeira rolagem após o hero.
4. SE houver alerta crítico O SISTEMA DEVE posicioná-lo antes de “Iniciar rota”, sem
   esconder o restante da navegação.

### RF-DES-03 — Aparência de aplicativo

**História:** Como visitante, quero uma navegação que se comporte e pareça um aplicativo
instalado, mantendo URLs compartilháveis e acessibilidade web.

1. QUANDO o visitante navegar no celular O SISTEMA DEVE oferecer cabeçalho compacto,
   abas contextuais aderentes e ações com alvo mínimo de 44 por 44 px.
2. QUANDO a navegação inferior for introduzida O SISTEMA DEVE manter Mapa e Catálogo
   como abas da rota e não como destinos globais.
3. QUANDO uma ação usar ícone O SISTEMA DEVE fornecer nome acessível e estado
   perceptível sem depender apenas de cor.
4. QUANDO `prefers-reduced-motion` estiver ativo O SISTEMA DEVE remover transições
   não essenciais.

### RF-DES-04 — Ritmo e legibilidade responsivos

**História:** Como visitante, quero ler e operar a interface com conforto em celulares
pequenos e grandes.

1. QUANDO a largura for menor que 48 rem O SISTEMA DEVE usar margens laterais de
   16 px e ritmo vertical baseado em 8, 12, 16 e 24 px.
2. QUANDO blocos relacionados forem empilhados O SISTEMA NÃO DEVE introduzir lacunas
   maiores que 24 px sem mudança real de seção.
3. QUANDO o texto do usuário estiver ampliado para 200% O SISTEMA DEVE preservar
   conteúdo, ordem de leitura e ações essenciais sem sobreposição.

### RF-DES-05 — Descoberta de rotas com aparência de aplicativo

**História:** Como visitante, quero comparar rotas em uma tela móvel compacta e visual,
sem percorrer um cabeçalho e um formulário excessivamente altos.

1. QUANDO a listagem de rotas abrir no celular O SISTEMA DEVE apresentar região,
   título, troca de região, busca e resultado antes dos cards sem lacunas excessivas.
2. QUANDO filtros forem exibidos entre 320 e 480 px O SISTEMA DEVE manter a busca em
   destaque e agrupar dificuldade e duração em uma grade compacta quando houver espaço.
3. QUANDO uma rota for listada O SISTEMA DEVE destacar nome, promessa, dificuldade,
   duração e disponibilidade offline sem inventar fotografia ou informação editorial.
4. QUANDO o tema estiver claro ou escuro O SISTEMA DEVE preservar a mesma hierarquia,
   contraste e aparência de aplicativo.

## Casos de borda

- Título de rota com duas ou três linhas.
- Custo ausente ou apresentado como “Consulte localmente”.
- Alerta crítico com descrição longa.
- Download offline em progresso, concluído, desatualizado ou indisponível.
- Preferência de movimento reduzido e contraste forçado.
- Celular de 320 px de largura e orientação paisagem.
- Conteúdo sem fotografia publicada: usar superfície editorial, sem imagem fictícia.
- Região com nome longo e apenas uma rota publicada.

## Requisitos relacionados

- `RF-03`, `RF-04`, `RF-06` e `RF-07` da spec `plataforma-mvp`.
- `RNF-01` (WCAG 2.2 AA) e `RNF-02` (desempenho móvel).
