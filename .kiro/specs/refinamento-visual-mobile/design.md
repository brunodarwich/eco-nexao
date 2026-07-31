# Design — refinamento visual mobile e tema escuro

> Status: implementado  
> Atualizado em: 2026-07-29

## Diagnóstico da interface atual

No breakpoint móvel, `.route-hero` muda para uma coluna, mas mantém `gap` de 32 px.
Os três fatos da rota também viram três cards verticais. A isso se somam a nota de
atualização, as ações locais, a barra de abas, `gap` de 48 px em `.route-tab-content`
e `padding` vertical de 48 px em cada `.route-section`.

O problema não é um único `margin`, mas a soma de espaçamentos de desktop e grupos
visuais redundantes. Apenas reduzir todos os valores deixaria a interface apertada sem
melhorar a hierarquia.

## Direção visual

### Conceito

**Noite amazônica:** base quase preta e neutra, superfícies discretamente esverdeadas e
cores vivas apenas onde ajudam a decidir ou se orientar.

| Papel | Proposta escura | Uso |
|---|---:|---|
| `background` | `#090D09` | fundo principal |
| `surface` | `#101610` | conteúdo contínuo |
| `surface-raised` | `#171F17` | cards, abas e controles |
| `surface-interactive` | `#1D281D` | hover/pressed/seleção suave |
| `text` | `#F5F7F3` | títulos e texto principal |
| `text-muted` | `#AFB9AC` | metadados |
| `border` | `#2B382B` | divisores e limites |
| `primary` | `#93BD72` | CTA e estado ativo |
| `primary-strong` | `#B0D78E` | hover e foco |
| `accent` | `#F8C900` | alerta, foco e orientação pontual |

Os valores deverão ser validados por contraste antes da implementação. Nenhum componente
deve receber cores literais; os tokens entram em `packages/ui`.

## Estrutura proposta para o detalhe mobile

1. **App bar compacta:** voltar, nome da rota, compartilhar e favorito.
2. **Hero curto:** fotografia editorial opcional, etiqueta da região e promessa.
3. **Resumo em uma linha:** duração, dificuldade e custo como chips ou células compactas.
4. **Ação principal:** `Iniciar rota`; alertas críticos aparecem imediatamente antes.
5. **Ações secundárias:** favorito e offline em botões compactos.
6. **Abas aderentes:** Visão geral, Mapa e Catálogo, preservando as URLs atuais.
7. **Preparação escaneável:** Como chegar, O que levar e Melhor horário em linhas
   acionáveis ou grupos expansíveis.
8. **Etapas:** linha do tempo compacta, com mapa como ação contextual.

## Estrutura da listagem mobile

1. **Cabeçalho global compacto:** logo e ação explícita para alternar o tema.
2. **Introdução territorial:** região ativa, título, descrição e troca de região em um
   único bloco de leitura, sem vazio vertical.
3. **Filtros densos:** busca em largura total; dificuldade e duração lado a lado a partir
   de 360 px; contagem e limpeza próximas aos controles.
4. **Card de rota editorial:** faixa visual criada somente com tokens, estado de
   publicação/offline, metadados, promessa e CTA. Fotografias só entram quando fizerem
   parte do contrato publicado.

O tema claro usa a mesma composição para evitar que a tela pareça uma versão antiga. O
controle de tema comunica a ação seguinte (`Usar escuro` ou `Usar claro`), enquanto o nome
acessível informa estado atual e destino.

### Orçamento de altura no celular

Para viewport de 390 × 844 px, sem alerta crítico:

| Bloco | Altura-alvo |
|---|---:|
| app bar | 56 px |
| hero visual + promessa | 220–280 px |
| fatos | 56–64 px |
| ações | 104–116 px |
| abas | 48–52 px |
| início da preparação | deve aparecer até aproximadamente 720 px de conteúdo |

O orçamento é uma referência de composição, não uma altura fixa. Texto ampliado deve
refluir naturalmente.

## Navegação mobile

- A app bar substitui o cabeçalho de desktop dentro do contexto da rota.
- As abas da rota podem usar `position: sticky` abaixo da área segura.
- A navegação global inferior é uma evolução recomendada para `Início`, `Rotas`,
  `Salvos` e `Perfil`, mas sua introdução depende de completar os destinos e testar
  sobreposição com teclado e áreas seguras.
- `Mapa` e `Catálogo` permanecem contextuais à rota.

## Componentes a evoluir

- `RouteAppBar`
- `RouteHeroCompact`
- `RouteFactStrip`
- `RoutePrimaryActions`
- `StickyRouteTabs`
- `PreparationList`
- `RouteStageTimeline`
- `MobileBottomNavigation` (fase posterior)

Desktop continuará usando a mesma informação com composição em duas colunas. A mudança
de componente não altera os contratos públicos da API.

## Acessibilidade

- Contraste AA para texto normal e componentes de interface.
- Foco visível com `accent`, sem remover outline por estilo.
- Alvos de toque mínimos de 44 px.
- Abas identificadas como navegação e estado atual por `aria-current`.
- Ícones decorativos ocultos; ícones de ação com nome acessível.
- Hero fotográfico não carrega informação exclusiva.
- Ordem DOM segue app bar, resumo, alerta, ações, abas e conteúdo.
- Layout validado com zoom de 200%, contraste forçado e movimento reduzido.

## Desempenho

- Hero usa imagem responsiva, dimensões reservadas e carregamento priorizado somente no
  detalhe da rota.
- Ícones devem ser SVGs locais ou biblioteca já aprovada, sem fonte de ícones.
- Abas aderentes e gradientes usam CSS; nenhum efeito pesado de blur.
- A fotografia não é obrigatória para a primeira entrega do refinamento.

## Mockups de referência

- `docs/design-proposals/econexao-dark-mobile-board-v1.png`
- `docs/design-proposals/econexao-dark-route-pindobal-v1.png`

Os mockups são direção visual, não fonte de conteúdo factual. Fotografias, nomes de
atores, avaliações e pontos mostrados neles são ilustrativos e não podem ser publicados
sem curadoria humana.

## Estratégia de verificação

- Testes de componentes para tema, estado das abas e ações locais.
- E2E nos viewports 320 × 568, 390 × 844 e 430 × 932.
- Capturas comparativas claro/escuro para hero, alertas, mapa e catálogo.
- Axe ou equivalente automatizado, seguido de teclado, leitor de tela e zoom manuais.
- Medição de LCP, CLS e INP na rota de Pindobal.
