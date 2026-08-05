# Visão de arquitetura

A ECOnexão é um monorepo multirregional com experiência pública sem conta obrigatória,
operação editorial protegida e uma API como única porta de acesso aos dados.

## Componentes existentes

| Caminho                       | Responsabilidade                                                   | Tecnologia                 |
| ----------------------------- | ------------------------------------------------------------------ | -------------------------- |
| `apps/web`                    | PWA pública, rotas, catálogo, mapa e pacote offline                | Next.js, React, TypeScript |
| `apps/admin`                  | painel operacional e fluxos editoriais                             | Next.js, React, TypeScript |
| `services/api`                | domínio, autenticação, importação, publicação, auditoria e relatos | Django, DRF, GeoDjango     |
| `packages/ui`                 | tokens, estilos e componentes compartilhados                       | React e CSS                |
| `packages/contracts`          | OpenAPI e tipos TypeScript derivados                               | OpenAPI                    |
| `packages/config`             | configurações compartilhadas                                       | TypeScript e ESLint        |
| `tools/development_dashboard` | leitura local das tarefas das specs                                | Streamlit                  |

## Fluxo principal

```text
visitante ──> apps/web ──> API pública ──> conteúdo publicado
equipe     ──> apps/admin ──> API administrativa ──> revisão/publicação/auditoria
CSV/IA/automação ──> rascunho ──> revisão humana ──> publicação
```

O frontend não acessa o banco diretamente. O backend usa PostgreSQL/PostGIS no Supabase e
essa decisão também vale para desenvolvimento e integração: não há PostgreSQL/PostGIS local em
Docker. Processos web e admin alcançam o Django por HTTP; somente o Django recebe `DATABASE_URL`.
O backend mantém APIs versionadas sob `/api/v1`. Conteúdo público é versionado; operações editoriais
possuem escopo regional e trilha de auditoria.

## Limites do MVP

- Região é entidade do domínio; locais do piloto não são fixados na arquitetura.
- Localização é opcional, solicitada sob demanda e permanece no dispositivo.
- Analytics depende de consentimento e não recebe coordenadas nem dados pessoais.
- O mapa possui alternativa textual; tema claro é padrão e o escuro é equivalente.
- Integrações externas apoiam descoberta editorial, mas não bloqueiam a experiência pública.
- Importações e IA criam rascunhos; somente pessoas autorizadas publicam.

## Contratos e dados

A API Django é a fonte do OpenAPI. Use `pnpm contracts:generate` para regenerar schema e tipos
e `pnpm contracts:check` para detectar divergências. O modelo de dados e o CSV canônico estão
descritos em [`spec/04-modelo-dados-csv.md`](../../spec/04-modelo-dados-csv.md).

As decisões completas estão em [`.kiro/specs/plataforma-mvp/design.md`](../../.kiro/specs/plataforma-mvp/design.md)
e em [`spec/03-backend-python-apis.md`](../../spec/03-backend-python-apis.md).
