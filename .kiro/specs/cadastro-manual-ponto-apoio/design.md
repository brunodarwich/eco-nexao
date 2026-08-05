# Design — Cadastro manual administrativo de ponto de apoio

> Status: aprovado para implementação
> Depende de: `requirements.md` aprovado

## Visão geral

Uma única operação administrativa cria um agregado privado e auditado. Ela reutiliza autenticação,
CSRF, autorização, proxy, auditoria e workflow existentes. O endpoint não chama publicação: após
o `201`, o ator em `draft` passa a ser um alvo existente e pode seguir pelo editor/revisões atuais.

```mermaid
sequenceDiagram
    actor E as Editor
    participant UI as Painel admin
    participant API as API administrativa
    participant DB as PostgreSQL/PostGIS
    E->>UI: Preenche e confirma
    UI->>API: POST + sessão + CSRF + Idempotency-Key
    API->>API: Autentica, autoriza, limita e valida
    API->>DB: Inicia transação e verifica duplicidade
    API->>DB: Cria Actor draft, Location, Contacts e RouteActors
    API->>DB: Cria AuditEvent minimizado e resultado idempotente
    DB-->>API: Commit único
    API-->>UI: 201 + agregado seguro
    UI-->>E: Rascunho criado; abrir no editor
```

## Decisões explícitas e alternativas

- **Agregado persistente:** criar `Actor` real em `draft`, não uma `EditorialRevision` sem alvo. A
  revisão atual exige alvo existente; após a criação, mudanças e publicação continuam no workflow.
- **Endpoint dedicado:** propor `POST /api/v1/admin/catalog/support-points/`. Um endpoint genérico de
  atores aumentaria o escopo para outros tipos e fica fora desta spec.
- **Ação dedicada:** usar `create_support_point`, concedida a `editor` e `administrator`.
  Reutilizar apenas `edit_content` reduziria a capacidade de revogação e auditoria granular.
- **Região única:** a localização e todos os vínculos pertencem à mesma região. A API resolve as
  referências no banco antes de autorizar.
- **Campos controlados:** `actor_kind`, `editorial_status` e `partnership_type` não entram no corpo;
  são fixados no servidor.
- **Geografia precisa:** exigir `boundary` e usar cobertura espacial, que inclui a fronteira.
  Região apenas com `center_point` não aceita cadastro manual até receber geometria confiável.
- **Contato:** o contrato aceita zero ou mais itens para não induzir preenchimento inventado.
  Todo item deve ser público, ter referência à planilha consolidada e verificação humana. A API
  registra o usuário autenticado como verificador; não exige autorização do titular. Contato privado fica fora desta operação:
  `value_encrypted` não será usado até existir spec de criptografia, rotação e recuperação de chave.
- **Duplicidade conservadora:** colisões exatas e prováveis retornam `409`; não há `force=true` nem
  merge automático.
- **Duplicidade determinística:** contato ou endereço normalizado idêntico bloqueia; nome exige
  similaridade de pelo menos 0,85 combinada a distância de até 100 metros. Proximidade isolada não
  bloqueia pontos diferentes no mesmo endereço ou complexo.
- **Identificadores:** o servidor gera `external_id=manual:<uuid>` e slug derivado do nome com
  sufixo técnico curto; nenhum dos dois é informado no cadastro.
- **Idempotência:** `Idempotency-Key` é obrigatória. A impressão digital usa corpo canônico, usuário
  e região. O resultado é persistido atomicamente, retido por 24 horas e só pode ser repetido pelo
  mesmo usuário e região.
- **Falha interna:** `500` usa envelope estável e `request_id`; detalhes ficam fora da resposta.

Essas decisões favorecem informação verificável: bloqueiam coordenada sem limite regional,
evitam contatos inventados e tratam sinais fortes de duplicidade sem considerar proximidade
isolada como prova.

## Componentes e responsabilidades

| Componente | Responsabilidade |
|---|---|
| `modules/catalog` | serializer, serviço transacional, duplicidade, endpoint e throttle |
| `modules/accounts` | nova ação, matriz de papel e escopo regional existente |
| `modules/audit` | ação allowlisted e metadados minimizados |
| `packages/contracts` | OpenAPI e tipos TypeScript gerados |
| `config.openapi_overlays` | mantém o contrato design-first durante a ativação incremental; a view real fica excluída da geração até reproduzir integralmente operação, headers e envelopes |
| `apps/admin/src/lib/admin-api.ts` | sessão, CSRF, idempotência e tradução de erros |
| `poi-editor-modal` ou componente extraído | etapas do formulário e estados acessíveis |

## Contrato OpenAPI proposto

Enquanto a Task 1 antecede a implementação do endpoint, a operação aprovada vive em
`packages/contracts/openapi/design-first.yaml` e é incorporada pelo hook de geração do
drf-spectacular. O hook falha se uma rota Django tentar gerar o mesmo path ou schema; nessa etapa,
o overlay deve ser removido e substituído pelas anotações reais, impedindo duas fontes silenciosas.
O fluxo oficial formata tanto o schema quanto os tipos antes de compará-los.

### Operação

`POST /api/v1/admin/catalog/support-points/`

Cabeçalhos obrigatórios: cookie de sessão, `X-CSRFToken`, `Idempotency-Key` (UUID v4) e
`Content-Type: application/json`. Respostas incluem `Cache-Control: no-store` e `request_id` no
envelope de erro.

### Corpo da requisição

```yaml
actor:
  category_id: uuid
  public_name: string
  legal_name: string
  short_description: string
  full_description: string
  services: [string]
location:
  label: string
  address_fields: object
  latitude: number
  longitude: number
  public_visibility: boolean
contacts:
  - channel_type: phone|whatsapp|email|website|instagram
    value: string
    is_public: boolean
    source_type: consolidated_sheet|tourism_inventory|other_public
    source_reference: string
    verified_at: date-time
route_links:
  - route_id: uuid
    stage_id: uuid|null
    route_role: experience|support|start|stop|emergency|service
    editorial_position: integer
    is_featured: boolean
    sponsorship_label: string
```

`region_id` não é aceito como fonte de autoridade: a região é derivada da rota e conferida contra
a localização. Caso a implementação precise recebê-la para desambiguar a validação espacial, ela
continua sendo somente uma alegação conferida no servidor.

### Resposta `201`

```yaml
id: uuid
actor_kind: support
editorial_status: draft
partnership_type: editorial
region_id: uuid
location_id: uuid
contact_ids: [uuid]
route_links:
  - id: uuid
    route_id: uuid
    stage_id: uuid|null
created_at: date-time
```

A resposta não devolve `legal_name`, valores privados de contato, autorização, endereço completo
nem coordenadas. A UI conserva sua cópia local somente enquanto necessário e recarrega o editor
por endpoint autorizado.

### Erros

| Status | Código exemplificativo | Condição |
|---:|---|---|
| 400 | `validation_error`, `invalid_relation`, `invalid_csrf` | sintaxe, campo, relação ou CSRF inválido conforme convenção real |
| 401 | `authentication_required` | sessão ausente ou expirada |
| 403 | `permission_denied` | ação ou escopo regional ausente |
| 409 | `duplicate_support_point`, `idempotency_conflict`, `concurrent_conflict` | duplicidade ou concorrência |
| 429 | `rate_limited` | limite excedido; inclui `Retry-After` |
| 500 | `internal_error` | falha inesperada segura e rollback integral |

O schema deve usar o envelope de erro já padronizado no repositório. A convenção atual de CSRF
deve ser confirmada por teste real: se DRF produzir `403`, o OpenAPI e os critérios serão alinhados
explicitamente antes da implementação, sem mascarar a resposta.

## Validação e normalização

`support_point_serializers.py` rejeita campos desconhecidos e normaliza somente representações
sem alterar o conteúdo público. `support_point_relations.py` resolve categoria, rotas, etapas e
região no banco, aplica o escopo antes de consultar candidatos e constrói o ponto geográfico.
`support_point_duplicates.py` retorna somente IDs técnicos e códigos de sinais, nunca os valores
que causaram a correspondência.

- Aplicar limites dos modelos (`public_name` 160, `legal_name` 200, `short_description` 180,
  `slug` 140, `external_id` 160) e um limite total de corpo configurável; slug e `external_id` são
  saídas geradas, nunca entradas deste endpoint.
- Normalizar whitespace e case para comparação sem alterar silenciosamente o texto público.
- Validar UUIDs antes da consulta; categoria deve estar ativa.
- Construir `Point(longitude, latitude, srid=4326)` somente depois de validar números finitos e
  faixas; exigir `boundary` e validar com cobertura espacial, incluindo a fronteira.
- Telefones/WhatsApp: E.164; e-mail: formato e normalização; website/Instagram: URL HTTPS, sem
  credenciais e com host válido. A decisão de aceitar handle de Instagram exigiria mudança de
  contrato e não é assumida.
- Rejeitar duplicatas internas de contato e vínculo antes de escrever.
- Rota deve pertencer à região; etapa opcional deve pertencer à rota; posição deve ser positiva.

## Duplicidade e idempotência

1. Validar a chave e procurar registro idempotente sob lock.
2. Se existir com o mesmo fingerprint, devolver o resultado anterior; se divergir, `409`.
3. Sob transação, consultar colisões exatas (`external_id`, `slug`, constraints) e candidatos
   prováveis no escopo permitido: contato/endereço normalizado idêntico ou nome com similaridade
   mínima de 0,85 em até 100 metros.
4. Criar o agregado, auditoria e registro idempotente; constraints são a última barreira contra
   corrida.
5. Converter `IntegrityError` conhecido em `409`; exceções desconhecidas geram rollback e `500`.

No primeiro corte, textos são comparados após `casefold`, remoção de diacríticos e compactação de
espaços; nomes usam `SequenceMatcher` determinístico. Endereços comparam apenas a estrutura
allowlisted normalizada. Contatos privados não participam da busca nem são aceitos por esta
operação. Registros legados malformados são ignorados sem expor ou registrar seus valores.

O registro idempotente expira após 24 horas e pertence ao par usuário/região. O fingerprint nunca
é o payload bruto e não deve permitir reconstruir contatos. Um job idempotente pode expurgar
registros vencidos sem afetar atores criados.

## Transação, concorrência e rollback

`SupportPointIdempotencyRecord` usa chave UUID globalmente única, usuário, região, fingerprint
SHA-256, resposta mínima e expiração. O serviço bloqueia a linha de `Region` antes de repetir a
detecção de duplicidade e inserir o agregado, serializando criações concorrentes na mesma região.
O registro idempotente e `AuditEvent` pertencem à mesma transação do ator.

- Usar uma única `transaction.atomic` para todos os registros e auditoria.
- Resolver e bloquear referências em ordem determinística: categoria, região derivada, rotas e
  etapas; depois verificar duplicidade e inserir o agregado.
- Não realizar chamadas externas dentro da transação.
- Constraints únicas existentes permanecem a defesa final; novas constraints/migration devem ser
  reversíveis e testadas em PostgreSQL/PostGIS.
- Falha em qualquer suboperação, inclusive auditoria e idempotência, reverte tudo.
- O rollback operacional é a exclusão controlada de um rascunho nunca publicado ou sua correção
  pelo workflow; esta spec não autoriza apagar histórico publicado.

## Segurança, privacidade e auditoria

- Reutilizar sessão Django e CSRF. A operação usa `AdminSessionAuthentication`, especialização que
  declara o desafio `Session` para distinguir ausência de identidade (`401`) de identidade sem
  ação ou escopo (`403`), sem mudar a autenticação global dos endpoints existentes.
- Um mixin obrigatório reúne `HasAdminAction`, ação dedicada, parser limitado e os dois throttles;
  a view de criação reutiliza esse mixin e não reconstrói essas proteções separadamente.
- Nova ação `CREATE_SUPPORT_POINT`, concedida explicitamente a `editor` e `administrator`; nenhum
  papel herda por hierarquia implícita.
- O escopo regional é conferido novamente depois que as rotas determinarem a região no servidor;
  dados enviados pelo cliente nunca concedem acesso.
- Throttles configuráveis e independentes limitam usuário autenticado e origem, com padrões de
  `20/hour` e `60/hour`; a resposta DRF inclui `429` e `Retry-After`.
- O parser limita o JSON a 64 KiB mesmo sem `Content-Length`; o contrato e constantes limitam o
  primeiro corte a 10 contatos públicos e 20 vínculos de rota.
- Auditoria proposta `catalog.support_point.create` com allowlist: `actor_id`, `region_id`,
  `route_link_ids`, contagens, `request_id`, `result` e indicação de replay idempotente.
- Não registrar payload, nome, endereço, coordenadas, contato, texto descritivo ou referência de
  autorização. Traces e erros recebem somente IDs técnicos.
- Resultados de duplicidade fora do escopo são indistinguíveis de uma negação genérica e nunca
  revelados.

## Fluxo da interface administrativa

1. O botão aparece somente quando a sessão informa a ação proposta; ausência de botão não substitui
   autorização no servidor.
2. O diálogo reutiliza o hook acessível compartilhado e inicia em Dados básicos.
3. As etapas validam localmente para feedback, mas o servidor é autoritativo.
4. O resumo identifica que o resultado será `Rascunho` e não oferece publicação.
5. Ao confirmar, o cliente gera uma chave UUID v4, reutilizada em novas tentativas do mesmo
   formulário/payload após timeout.
6. `400` destaca campos; `409` mostra conflito sem opção de forçar; `401/403` orientam sessão ou
   permissão; `429` respeita `Retry-After`; `500` permite tentar de novo com a mesma chave.
7. Somente `201` dispara `onSave`, fecha o diálogo e atualiza a lista. O botão opcional “Abrir
   rascunho” usa o editor persistente existente.

## Estratégia de testes

### Backend

- Serializer e serviço: limites, enums, UUIDs, coordenadas, geometria aprovada, contatos, URLs,
  categoria, rotas, etapas e cardinalidades.
- Matriz: anônimo `401`; papel/ação/escopo inválidos `403`; editor autorizado `201`.
- CSRF real, throttling `429`, `no-store` e resposta `500` segura.
- Atomicidade por falha injetada em cada suboperação e auditoria; banco permanece sem parcial.
- Idempotência após timeout, chave divergente, constraints e duas requisições concorrentes.
- Duplicidade exata/provável dentro do escopo e não divulgação fora dele.

### Contrato

- Validar respostas HTTP reais `201`, `400`, `401`, `403`, `409`, `429` e `500` contra OpenAPI.
- Regenerar tipos e executar `pnpm contracts:check`.

### Frontend

- Formulário por etapas, validação, resumo `Rascunho`, ausência de publicação e payload correto.
- Estados para todos os códigos, preservação de dados, mesma chave em retry, prevenção de duplo
  envio e `onSave` apenas após `201`.
- Foco, Escape, restauração, teclado, anúncios e temas.

### E2E

- Serviços separados: login de editor, seleção de região/rota, cadastro, reload e abertura no
  editor existente, comprovando ausência no catálogo público.
- Cenários de sessão expirada, CSRF, conflito, throttle, API indisponível e retry idempotente.
- Desktop/mobile, teclado e zoom 200%, sem mocks do comportamento sob teste.

## Migração e implantação

1. Requirements, design e P-CMPA-01 a 05 aprovados em 2026-08-05.
2. Aplicar migrations reversíveis de idempotência/constraints, se necessárias.
3. Implantar API e contrato antes de habilitar o botão.
4. Manter o botão protegido por capacidade retornada pela sessão; não simular sucesso.
5. Executar smoke test com dados fictícios e confirmar invisibilidade pública.
6. Rollback da aplicação desabilita a UI e endpoint; migrations preservam registros já criados.

## Observabilidade

- Contadores por resultado (`201/400/401/403/409/429/500`), duração e região técnica.
- Alerta para aumento de conflitos, throttling e rollback interno.
- `request_id` correlaciona API e auditoria, sem PII ou coordenadas.

## Matriz de rastreabilidade

| Requisito | Componentes | Verificação principal |
|---|---|---|
| RF-CMPA-01, RB-CMPA-01/03 | catalog, audit | criação integral em draft e rollback |
| RF-CMPA-02, RB-CMPA-02 | accounts, catalog | matriz de papel/ação/região |
| RF-CMPA-03 | endpoint, throttle, admin-api | CSRF e `429` sem escrita |
| RF-CMPA-04 | serializers, domínio | tabela de entradas válidas/inválidas |
| RF-CMPA-05, RB-CMPA-04 | serviço, idempotência | concorrência e replay |
| RF-CMPA-06 | audit | allowlist e falha transacional |
| RF-CMPA-07 | painel | componentes e E2E real |
| RF-CMPA-08, RNF-CMPA-04 | contracts | respostas reais contra OpenAPI |
| RNF-CMPA-01 | serviço e banco | transação, constraints e rollback |
| RNF-CMPA-02 | accounts, audit, logs | segurança e minimização |
| RNF-CMPA-03 | painel e UI compartilhada | WCAG 2.2 AA |
