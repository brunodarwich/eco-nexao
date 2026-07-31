# Direção técnica

## Arquitetura-alvo

- Frontend público: React + TypeScript com Next.js App Router para PWA, SEO e links compartilháveis.
- Backend: monólito modular Python com Django e Django REST Framework.
- Dados: PostgreSQL + PostGIS e GeoDjango.
- Administração: aplicação protegida consumindo APIs administrativas; Django Admin pode apoiar a fase inicial sem substituir fluxos editoriais.
- Jobs: interface assíncrona desde o início; Celery + Redis quando importações, mídia e agregações exigirem.
- Cache: HTTP/CDN para conteúdo público e Redis quando necessário.
- Fontes externas: adaptadores server-side opcionais para descoberta editorial; nunca dependências da experiência pública.
- Testes: pytest/pytest-django no backend; testes unitários, componentes e E2E no frontend.

## Limites

- Frontend nunca acessa o banco diretamente.
- APIs públicas e administrativas são versionadas.
- Conteúdo publicado é versionado e pode sofrer rollback.
- Eventos de analytics passam por allowlist e consentimento.
- Localização precisa permanece no dispositivo no MVP.
- Conteúdo de provedores externos respeita termos, atribuição e retenção; somente dados verificados entram no domínio publicado.

## Qualidade mínima

- TypeScript em modo estrito.
- Formatação e lint automatizados.
- Migrations revisáveis e reversíveis.
- Testes de autorização para todas as ações administrativas.
- Contratos de API documentados.
- Observabilidade sem dados pessoais.

Referência completa: `spec/03-backend-python-apis.md`.
