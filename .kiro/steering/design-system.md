# Sistema visual ECOnexão

## Identidade

A marca usa fotografia de folhas e gotas combinada a verdes e amarelo. O produto deve ser predominantemente branco ou cinza muito claro; a paleta aparece em detalhes, ações, indicadores e áreas de destaque.

Fonte da paleta: `Logo-ECOnexão.pdf`, página 3.

## Cores da marca

| Token base | Valor | Uso recomendado |
|---|---:|---|
| `brand-forest` | `#33601E` | ação principal, links, foco |
| `brand-deep` | `#1C3B0F` | textos de destaque e tema escuro |
| `brand-leaf` | `#5D8D3E` | estados positivos e gráficos |
| `brand-sage` | `#759B71` | bordas, áreas suaves, ícones |
| `brand-sun` | `#F8C900` | destaque, foco e chamada pontual |

## Tema claro

| Token semântico | Valor |
|---|---:|
| `background` | `#F7F8F5` |
| `surface` | `#FFFFFF` |
| `surface-subtle` | `#EFF2EC` |
| `surface-raised` | `#FFFFFF` |
| `surface-interactive` | `#E5EADF` |
| `text` | `#172015` |
| `text-muted` | `#5E695A` |
| `border` | `#DDE3D9` |
| `primary` | `#33601E` |
| `primary-hover` | `#1C3B0F` |
| `accent` | `#F8C900` |

## Tema escuro

| Token semântico | Valor |
|---|---:|
| `background` | `#090D09` |
| `surface` | `#101610` |
| `surface-subtle` | `#141C14` |
| `surface-raised` | `#171F17` |
| `surface-interactive` | `#1D281D` |
| `text` | `#F5F7F3` |
| `text-muted` | `#AFB9AC` |
| `border` | `#2B382B` |
| `primary` | `#93BD72` |
| `primary-hover` | `#B0D78E` |
| `accent` | `#F8C900` |

## Tipografia, overlays e elevação

- Pilha: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial,
  sans-serif`.
- Escala: `display-sm` 32/36, `heading-xl` 28/32, `heading-lg` 24/30,
  `heading-md` 20/26, `title` 18/24, `body` 16/24, `label` 14/20 e `caption` 12/16.
- Overlays semânticos: `overlay-soft`, `overlay-strong` e `scrim`; warning usa
  `warning`, `warning-surface` e `warning-border`.
- Elevação: `shadow-sm` para superfícies elevadas e `shadow-sheet` para painéis móveis.
- Ícones: biblioteca Lucide, SVG com `currentColor`, grade de 24 px e licença ISC.

## Regras de tema

- Preferência inicial: tema claro.
- Escolha explícita do usuário prevalece e é persistida localmente.
- O controle de tema deve ter nome acessível e indicar o estado atual.
- A meta `theme-color` deve acompanhar o tema.
- Nunca dependa só de cor para comunicar estado.
- Texto normal e controles devem atingir contraste WCAG 2.2 AA.
- A logo horizontal transparente é a preferência em cabeçalhos; a quadrada é usada em ícones e telas compactas.

## Forma e movimento

- Cantos de 12 a 24 px, com superfícies limpas.
- Sombras discretas; bordas sustentam a hierarquia.
- Amarelo em pequenas doses para não competir com o conteúdo.
- Movimento respeita `prefers-reduced-motion`.
