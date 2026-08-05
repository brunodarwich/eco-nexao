# ECOnexão

Infraestrutura digital multirregional que conecta visitantes à oferta real dos destinos por
meio de rotas confiáveis, catálogo contextual, mapas e operação editorial rastreável.

O MVP é uma PWA pública sem conta obrigatória, acompanhada de painel protegido e API Django.
Pindobal é a rota demonstrativa inicial; regiões e localidades continuam entidades do domínio,
não valores fixos da plataforma.

## Começar

Pré-requisitos: Node.js 20.9+, pnpm 10, `uv`, GDAL/GEOS e acesso ao Supabase/PostGIS do ambiente.
O desenvolvimento e os testes integrados não usam PostgreSQL/PostGIS local em Docker. A API
Django acessa exclusivamente o Supabase configurado por `DATABASE_URL`; frontends nunca recebem a
conexão SQL. Testes que gravam fixtures exigem autorização explícita do projeto Supabase alvo e
devem limpar os dados fictícios mesmo quando falharem.

```powershell
pnpm install
uv sync --project services/api
Copy-Item .env.example .env
uv --cache-dir .uv-cache run --project services/api python services/api/manage.py migrate
pnpm dev:app
```

Configure apenas os placeholders necessários no `.env` local. Não versione nem exponha esse
arquivo. Instruções de banco, sessão, serviços separados e validação estão no
[guia de desenvolvimento](docs/development/setup.md).

## Serviços

| Serviço            | URL local                      | Comando              |
| ------------------ | ------------------------------ | -------------------- |
| PWA pública        | `http://localhost:3000`        | `pnpm dev:web`       |
| painel operacional | `http://localhost:3001`        | `pnpm dev:admin`     |
| API v1             | `http://localhost:8000/api/v1` | `pnpm dev:api`       |
| painel de specs    | `http://localhost:8501`        | `pnpm dev:dashboard` |

`pnpm dev:app` inicia PWA e API. `pnpm check` executa a verificação integrada do monorepo.

## Estrutura

```text
apps/web                    PWA pública Next.js
apps/admin                  painel operacional Next.js
services/api                API Django REST Framework
packages/ui                 componentes e tokens compartilhados
packages/contracts          OpenAPI e tipos gerados
packages/config             configurações compartilhadas
tools/development_dashboard acompanhamento local das specs
spec                        especificação detalhada do produto
.kiro                       direção e specs executáveis
docs                        guias, operação, apresentações e evidências
```

Veja a [visão de arquitetura](docs/architecture/overview.md) e o
[índice completo da documentação](docs/README.md).

## Desenvolvimento orientado por especificação

A fonte de verdade segue esta precedência:

1. [direção permanente](.kiro/steering/product.md);
2. [specs executáveis](.kiro/README.md);
3. [especificação consolidada](spec/README.md);
4. guias em `docs/` e READMEs dos componentes.

Antes de alterar comportamento ou arquitetura, atualize requirements, design e tasks da spec
ativa. Marque `[~]` durante a implementação e `[x]` somente depois de registrar a verificação.
Importações, automações e IA produzem rascunhos; apenas pessoas publicam.

## Operação e referências

- [operação demonstrativa de Pindobal](docs/operations/pindobal.md);
- [contratos da API](packages/contracts/README.md);
- [painel de acompanhamento](tools/development_dashboard/README.md);
- [sistema visual](.kiro/steering/design-system.md);
- [catálogo de materiais, apresentações e evidências](docs/README.md).

Os rascunhos e ativos originais mantidos na raiz são acervo de origem, não documentação
normativa. A classificação e a política de manutenção estão registradas no índice de `docs/`.
