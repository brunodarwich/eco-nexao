# Desenvolvimento local

## Pré-requisitos

- Node.js 20.9 ou superior;
- pnpm 10;
- `uv`;
- GDAL e GEOS — no Windows, OSGeo4W em `C:\OSGeo4W` é detectado;
- acesso ao banco Supabase/PostGIS do ambiente.

O repositório não provisiona PostgreSQL/PostGIS local em Docker. Desenvolvimento, migrations e
testes integrados usam o Supabase indicado por `DATABASE_URL`, carregado apenas pelo Django. Nunca
copie essa variável para `NEXT_PUBLIC_*`, logs ou comandos documentados.

Testes que criam fixtures devem confirmar explicitamente a referência pública do projeto alvo,
usar somente dados fictícios identificáveis e removê-los em `finally`. Não execute a integração
contra produção ou contra um projeto compartilhado sem autorização do responsável.

### Integração entre serviços — task 7.4

O comando `pnpm test:integration:services` usa as portas `18100` (Django API), `13100` (Next.js
web) e `13101` (Next.js admin). Ele exige `TASK_7_4_SUPABASE_PROJECT_REF` com a referência pública
do projeto autorizado, valida que o host da conexão Django corresponde a essa referência e não
imprime `DATABASE_URL`. Web, admin e API são processos separados; todo tráfego funcional é HTTP
real, sem mock de API.

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
