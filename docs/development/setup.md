# Desenvolvimento local

## Pré-requisitos

- Node.js 20.9 ou superior;
- pnpm 10;
- `uv`;
- GDAL e GEOS — no Windows, OSGeo4W em `C:\OSGeo4W` é detectado;
- acesso ao banco Supabase/PostGIS do ambiente.

O Python é gerenciado pelo `uv` e não precisa ser instalado globalmente.

## Instalação

Na raiz do repositório:

```powershell
pnpm install
uv sync --project services/api
Copy-Item .env.example .env
```

Preencha o `.env` local a partir das instruções e placeholders do exemplo. Use a conexão
Session pooler com `sslmode=require`. Nunca versione o `.env` e nunca exponha segredo,
`service_role` ou chave do backend com prefixo `NEXT_PUBLIC_`.

Depois de configurar o banco:

```powershell
uv --cache-dir .uv-cache run --project services/api python services/api/manage.py migrate
```

## Executar

```powershell
pnpm dev:web       # PWA em http://localhost:3000
pnpm dev:admin     # painel em http://localhost:3001
pnpm dev:api       # API em http://localhost:8000/api/v1
```

Para PWA e API em um único terminal:

```powershell
pnpm dev:app
```

Endpoints úteis: saúde em `http://localhost:8000/api/v1/health` e OpenAPI em
`http://localhost:8000/api/v1/schema/`.

## Sessão administrativa

No ambiente local, use `DJANGO_SECURE_COOKIES=false` e limite
`DJANGO_CSRF_TRUSTED_ORIGINS` à origem do painel. Em homologação ou produção, use HTTPS e
`DJANGO_SECURE_COOKIES=true`.

A sessão é server-side. O cliente obtém CSRF, realiza login e envia o token em
`X-CSRFToken`; somente equipe administrativa ativa e autorizada no escopo regional acessa os
fluxos protegidos.

## Qualidade

```powershell
pnpm check
```

O comando valida contrato gerado, lint, formatação, tipos, testes e builds. Para E2E da PWA:

```powershell
pnpm test:e2e
```

Operações específicas do piloto estão em [operação de Pindobal](../operations/pindobal.md).
