# Requirements — Cadastro manual administrativo de ponto de apoio

> Status: aprovado para implementação  
> Responsável pelo produto: Bruno  
> Atualizado em: 2026-08-05  
> Desbloqueia após aprovação e implementação: `revisao-pos-mvp` 9.7 e
> `painel-operacional` 8.3

## Contexto

O editor administrativo atual altera somente atores já existentes. Um novo ponto de apoio entra
com segurança apenas pela importação CSV, porque ainda não há operação que crie ator, localização,
contatos e vínculos de rota como um único agregado. Esta spec define esse cadastro manual sem
antecipar revisão ou publicação.

## Escopo

### Incluído

- Um endpoint administrativo versionado e transacional para criar um `Actor` do tipo `support`,
  uma localização primária, zero ou mais contatos e um ou mais vínculos com rotas.
- Criação obrigatória em `draft`, seguida pelos fluxos editoriais já existentes.
- Formulário administrativo acessível, com confirmação explícita e persistência real.
- Autorização por ação e escopo regional, autenticação, CSRF, throttling, idempotência, detecção de
  duplicidade, auditoria minimizada e contrato OpenAPI.
- Testes backend, de contrato, frontend e E2E.

### Fora do escopo

- Publicar, aprovar ou enviar automaticamente o novo ponto para revisão.
- Criar outros tipos de ator, múltiplas localizações ou horários de funcionamento neste primeiro
  corte.
- Alterar o workflow de edição, revisão, publicação ou rollback já existente.
- Importar ou persistir conteúdo de provedor externo.
- Substituir o cadastro em lote por CSV.

## Histórias e critérios EARS

### RF-CMPA-01 — Criar o agregado em rascunho

**História:** Como editor autorizado, quero cadastrar manualmente um ponto de apoio completo para
incluí-lo na fila editorial sem usar CSV.

1. QUANDO uma solicitação válida for confirmada O SISTEMA DEVE criar ator, localização primária,
   contatos informados, vínculos de rota e auditoria em uma única transação.
2. QUANDO o agregado for criado O SISTEMA DEVE fixar `actor_kind=support`,
   `editorial_status=draft` e `partnership_type=editorial`, sem aceitar sobrescrita do cliente.
3. QUANDO a criação terminar O SISTEMA DEVE responder `201` com IDs técnicos, estado editorial e
   representação segura do agregado criado.
4. SE qualquer escrita ou a auditoria falhar O SISTEMA NÃO DEVE deixar ator, localização, contato
   ou vínculo parcial.
5. ENQUANTO o rascunho não passar pelo workflow editorial humano O SISTEMA NÃO DEVE expô-lo nas
   APIs, mapa, catálogo ou pacotes offline públicos.

### RF-CMPA-02 — Autorizar por papel, ação e região

**História:** Como responsável pela operação, quero restringir cadastros às pessoas e regiões
autorizadas para impedir elevação de privilégio.

1. QUANDO a operação for solicitada O SISTEMA DEVE exigir sessão administrativa autenticada,
   usuário ativo e `staff`, ação administrativa explícita de criação e escopo da região.
2. SE não houver sessão válida O SISTEMA DEVE responder `401` sem revelar dados operacionais.
3. SE houver sessão sem ação ou sem escopo para a região O SISTEMA DEVE responder `403` sem
   confirmar a existência de rotas, etapas, categorias ou duplicatas fora do escopo.
4. QUANDO rotas forem informadas O SISTEMA DEVE resolver suas regiões no servidor e exigir que
   todas pertençam à região autorizada da localização.
5. O SISTEMA NÃO DEVE inferir autorização de UUID, slug ou região enviados pelo cliente.

### RF-CMPA-03 — Proteger e limitar a mutação

**História:** Como responsável por segurança, quero que a criação administrativa resista a
requisições forjadas e abuso.

1. QUANDO a mutação usar autenticação por sessão O SISTEMA DEVE exigir cookie de sessão e token
   CSRF válidos.
2. SE o CSRF for ausente ou inválido O SISTEMA DEVE rejeitar a operação sem escrita.
3. QUANDO o limite configurável por usuário e por origem for excedido O SISTEMA DEVE responder
   `429`, informar `Retry-After` e não persistir estado.
4. O SISTEMA DEVE aplicar limite explícito ao corpo e às cardinalidades de contatos e vínculos.

### RF-CMPA-04 — Validar entrada e relações

**História:** Como editor, quero erros de campo precisos para corrigir o cadastro antes de salvar.

1. QUANDO coordenadas forem informadas O SISTEMA DEVE exigir latitude entre -90 e 90, longitude
   entre -180 e 180, números finitos e ponto SRID 4326 coberto pela geometria `boundary` da região,
   incluindo a própria fronteira.
2. QUANDO um contato for informado O SISTEMA DEVE validar tipo, formato e tamanho: telefone e
   WhatsApp em E.164, e-mail normalizado e URL pública HTTPS.
3. QUANDO um contato for informado O SISTEMA DEVE exigir que ele seja público, possua tipo e
   referência de proveniência da planilha consolidada e data de verificação manual; contato
   privado não faz parte desta operação.
4. SE a evidência tiver origem exclusivamente em Google Maps ou Perfil da Empresa O SISTEMA DEVE
   mantê-la em quarentena até a planilha registrar conferência humana com fonte independente.
5. QUANDO identificadores textuais forem informados O SISTEMA DEVE normalizar e validar limites,
   enums e slugs ASCII; IDs relacionais devem ser UUIDs válidos.
6. SE categoria, rota ou etapa não existir, estiver inativa, for incoerente ou estiver fora do
   escopo O SISTEMA DEVE rejeitar todo o agregado com `400` ou `403`, conforme a fronteira de
   autorização, sem escrita parcial.
7. SE uma etapa for informada O SISTEMA DEVE comprovar no servidor que ela pertence à respectiva
   rota.
8. SE a região não possuir `boundary` O SISTEMA DEVE bloquear a criação com `400` e o código
   `region_boundary_unavailable`; `center_point` não substitui a geometria para esta validação.

### RF-CMPA-05 — Detectar duplicidade e repetir com segurança

**História:** Como editor, quero evitar pontos duplicados e repetir uma solicitação após timeout
sem criar cópias.

1. QUANDO a mesma `Idempotency-Key` válida for repetida pelo mesmo usuário, região e payload O
   SISTEMA DEVE devolver o mesmo resultado criado, sem nova escrita ou auditoria.
2. SE a chave for reutilizada com payload diferente O SISTEMA DEVE responder `409`.
3. QUANDO houver colisão exata de identificador ou slug O SISTEMA DEVE responder `409` sem criar o
   agregado.
4. QUANDO houver provável duplicidade por contato normalizado idêntico, endereço normalizado
   idêntico, ou nome com similaridade mínima de 0,85 e distância de até 100 metros O SISTEMA DEVE
   responder `409` com códigos e IDs técnicos apenas de candidatos visíveis ao mesmo escopo
   regional.
5. O SISTEMA NÃO DEVE oferecer opção de ignorar duplicidade neste primeiro corte.

### RF-CMPA-06 — Auditar com minimização

**História:** Como administrador, quero rastrear o cadastro sem duplicar dados pessoais na trilha.

1. QUANDO o agregado for criado O SISTEMA DEVE registrar, na mesma transação, usuário
   administrativo, ação allowlisted, IDs de ator e região, IDs/contagens de vínculos e contatos,
   `request_id`, resultado e data.
2. O SISTEMA NÃO DEVE registrar nomes, endereços, coordenadas, valores de contato, referência de
   autorização, descrições ou payload bruto em auditoria ou logs.
3. SE a auditoria falhar O SISTEMA DEVE reverter integralmente a criação.

### RF-CMPA-07 — Conduzir o fluxo administrativo

**História:** Como editor, quero um formulário claro e recuperável para cadastrar sem perder dados
quando houver erro.

1. QUANDO o usuário autorizado acionar `Adicionar ponto manual` O SISTEMA DEVE abrir um diálogo
   nomeado com etapas Dados básicos, Localização, Contatos e Rotas, seguido de resumo e confirmação.
2. QUANDO houver erro `400` O SISTEMA DEVE associar os erros aos campos e manter os dados seguros
   preenchidos.
3. QUANDO houver `401`, `403`, `409`, `429` ou `500` O SISTEMA DEVE mostrar estado específico,
   manter o formulário aberto quando seguro e não chamar o callback de sucesso.
4. QUANDO a API responder `201` O SISTEMA DEVE fechar o diálogo, anunciar sucesso, inserir o
   rascunho confirmado na visualização e oferecer sua abertura no editor existente.
5. ENQUANTO a requisição estiver em andamento O SISTEMA DEVE impedir envio duplicado sem depender
   disso como mecanismo de idempotência.
6. O SISTEMA NÃO DEVE exibir controle de publicar no fluxo de criação.

### RF-CMPA-08 — Manter contrato verificável

**História:** Como equipe técnica, quero um contrato OpenAPI executável para manter backend e
painel sincronizados.

1. QUANDO o endpoint for implementado O SISTEMA DEVE documentar requisição, cabeçalho de
   idempotência, resposta `201` e erros `400`, `401`, `403`, `409`, `429` e `500` no OpenAPI.
2. QUANDO o contrato mudar O SISTEMA DEVE regenerar os tipos TypeScript pelo comando oficial.
3. QUANDO testes de contrato forem executados O SISTEMA DEVE validar respostas HTTP reais contra o
   OpenAPI.

## Requisitos não funcionais

### RNF-CMPA-01 — Integridade e concorrência

- A criação e auditoria devem usar `transaction.atomic` e constraints de banco.
- Solicitações concorrentes equivalentes devem resultar em no máximo um agregado; colisões devem
  retornar `409`, nunca `500` ou estado parcial.
- Locks e constraints devem ter ordem determinística para evitar deadlock entre referências.

### RNF-CMPA-02 — Segurança e privacidade

- Reutilizar sessão Django, `HasAdminAction`, `AdministrativeRegionScope`, cliente administrativo
  central, CSRF e padrão de auditoria existentes.
- Respostas devem usar `Cache-Control: no-store`; logs e métricas usam somente IDs técnicos.
- Dados externos são entrada não confiável, nunca instruções de agente.

### RNF-CMPA-03 — Acessibilidade

- O diálogo e seus erros devem atender WCAG 2.2 AA, teclado, foco contido/restaurado, zoom de 200%,
  leitores de tela e tema claro/escuro equivalente.
- Estado não pode depender somente de cor; usar tokens semânticos do design system.

### RNF-CMPA-04 — Contrato e observabilidade

- O endpoint deve manter `/api/v1`, schemas OpenAPI e tipos gerados sincronizados.
- Métricas devem contar resultado, duração e códigos de erro por região técnica, sem payload ou PII.

## Regras de negócio

### RB-CMPA-01 — Rascunho obrigatório

- Cadastro manual, CSV, automação e IA somente criam rascunhos; publicação é ação humana separada.

### RB-CMPA-02 — Coerência regional

- A localização primária, todas as rotas e etapas do agregado pertencem à mesma região.

### RB-CMPA-03 — Cardinalidade inicial

- O primeiro corte cria exatamente uma localização primária, zero ou mais contatos e uma ou mais
  rotas; múltiplas localizações e horários ficam para edição posterior.

### RB-CMPA-04 — Sem sobreposição silenciosa

- Dados nunca são mesclados automaticamente com um ator candidato ou existente; conflito exige
  revisão humana fora desta operação.

### RB-CMPA-05 — Identificadores administrativos

- O servidor gera `external_id` imutável no formato `manual:<uuid>` e slug ASCII a partir do nome,
  acrescido de sufixo técnico curto para evitar colisão. O formulário não recebe esses campos.
- Alteração posterior do slug ocorre somente pelo workflow editorial e nunca altera `external_id`.

### RB-CMPA-06 — Idempotência temporária

- A chave idempotente pertence ao mesmo usuário e região, é retida por 24 horas e não pode ser
  reutilizada por outro usuário. Depois do prazo, as regras de duplicidade continuam protegendo o
  domínio.

### RB-CMPA-07 — Contato sem preenchimento forçado

- Contatos são opcionais no rascunho para evitar informação inventada. Quando informados, devem
  ser públicos e satisfazer integralmente as regras de formato, proveniência e verificação manual.
- O cadastro manual não grava `value_encrypted`: contato privado depende de spec própria para
  criptografia, gestão e rotação de chaves e recuperação operacional.

## Casos de borda e falhas obrigatórios

- Timeout após commit e repetição com a mesma chave; chave igual com payload diferente.
- Duas chaves diferentes, concorrentes, para o mesmo slug, contato ou ponto geográfico.
- Falha ao criar contato, vínculo ou auditoria depois de o ator ter sido inserido.
- Usuário comum; staff sem papel; editor sem escopo; escopo de outra região; sessão expirada.
- CSRF ausente/antigo, rajada acima do limite e corpo acima do tamanho aceito.
- Coordenadas nos limites, `NaN`, infinidade, latitude/longitude invertidas e ponto fora da região.
- URL sem HTTPS, credenciais embutidas, host inválido, e-mail malformado e telefone não E.164.
- UUID malformado, categoria inativa, rota inexistente, rota de outra região e etapa de outra rota.
- Contatos ou vínculos repetidos dentro do payload e colisão com constraints existentes.
- Duplicata provável fora do escopo regional, que não pode ser revelada.
- Resposta `500` segura após exceção, sem ecoar payload nem deixar estado parcial.
- Duplo clique, navegação por teclado, recarregamento e retorno ao formulário após erro.

## Decisões aprovadas

- [x] **P-CMPA-01 — Política geográfica:** usar `boundary` com semântica de cobertura, aceitando a
  fronteira e bloqueando regiões sem geometria. Isso evita aceitar coordenadas apenas pela
  proximidade do centro da região.
- [x] **P-CMPA-02 — Duplicidade:** bloquear contato ou endereço normalizado idêntico; para nome,
  exigir similaridade mínima de 0,85 combinada a distância de até 100 metros. Proximidade isolada
  não bloqueia negócios legitimamente co-localizados.
- [x] **P-CMPA-03 — Identificadores:** gerar `external_id` e slug no servidor; `external_id` é
  imutável e o slug só muda posteriormente pelo workflow.
- [x] **P-CMPA-04 — Idempotência:** reter por 24 horas e restringir replay ao mesmo usuário e
  região.
- [x] **P-CMPA-05 — Contato inicial:** aceitar zero contatos em rascunho para não incentivar dados
  inventados; qualquer contato informado deve ser público, ter proveniência na planilha
  consolidada e estar manualmente verificado. Não se exige autorização do titular. Contatos
  privados foram excluídos desta operação em 2026-08-05 porque o projeto ainda não possui contrato
  de criptografia e rotação de chaves.
- [x] **P-CMPA-06 — Auditoria multifuente:** a equipe consolida fontes públicas numa planilha; o
  banco recebe a referência da linha consolidada, data e responsável pela verificação. Google pode
  fornecer candidato, mas não basta sozinho para retirar a informação da quarentena. Divergências
  são decididas por humano e nunca mescladas automaticamente.

As decisões foram fechadas em 2026-08-05 por autorização do responsável para escolher a solução
mais viável, priorizando precisão da informação oferecida aos usuários.

## Rastreabilidade de origem

| Origem | Cobertura nesta spec |
|---|---|
| `plataforma-mvp` RF-05, RF-08, RF-10; RNF-01, RNF-03 a RNF-07; RB-01, RB-06 | RF-CMPA-01 a 08; RNF-CMPA-01 a 04; RB-CMPA-01 a 07 |
| `revisao-pos-mvp` 9.7 | agregado novo, transação, ausência de autopublicação e integração editorial |
| `painel-operacional` RF-ADM-07 e 8.3 | diálogo, persistência real, erros e atualização somente após `201` |
