# Requirements - Painel Operacional Administrativo (Reflexo do App)

> Status: em revisão pós-integração em 2026-08-05

## Contexto

O painel administrativo (`apps/admin`) exibia como tela principal a ferramenta de consulta de candidatos do Google Places. O responsável pelo produto (com perfil TDAH) precisa de um painel operacional que seja o reflexo real do aplicativo ECOnexão: exibindo engajamento de visitantes, rotas mais acessadas, pontos de apoio mais clicados, estado editorial de publicação e alertas da comunidade, reduzindo sobrecarga cognitiva e orientando a ação prioritária.

## Escopo

- Redesenho completo da tela principal de `apps/admin`.
- Navegação estruturada em 5 abas claras: Métricas do App, Rotas & Prontidão, Central de Relatos &
  Alertas, Importar CSV e Descoberta Externa (Google Places).
- Hero Card de Foco Recomendado no topo ("Próxima Ação Prioritária").
- Métricas e ranqueamento de engajamento dos pontos/estágios das rotas.
- Acessibilidade WCAG 2.2 AA e perspicuidade visual para TDAH (ícone + texto + cor).

## Histórias e critérios EARS

### RF-ADM-01 - Foco Recomendado (TDAH)
**História:** Como operador do produto, quero ver imediatamente qual a ação prioritária do dia ao abrir o painel para não me sentir sobrecarregado.

1. QUANDO o painel operacional for aberto O SISTEMA DEVE exibir no topo um card de Hero com a ação prioritária recomendada.
2. SE houver alertas de segurança ou rotas pendentes O SISTEMA DEVE destacá-los com atalhos diretos de ação.
3. ENQUANTO os contratos administrativos não fornecerem contagens confiáveis O SISTEMA NÃO DEVE
   declarar a operação estável; deve informar que a prioridade consolidada está indisponível.
4. O SISTEMA DEVE fornecer o endpoint administrativo `/api/v1/admin/dashboard/summary` autenticado e autorizado por escopo regional para retornar contadores agregados sem PII.
5. Os contadores DEVEM categorizar:
   - Alertas ativos (`active_alerts_count`): relatos públicos com `status = pending` e `report_type = safety_warning`.
   - Relatos prioritários (`priority_reports_count`): relatos públicos com `status = pending` e `report_type` em `['safety_warning', 'closed_location']`.
   - Revisões pendentes (`pending_revisions_count`): revisões editoriais com `status = review`.
6. O Hero SOMENTE DEVE declarar a operação estável quando os contadores reais retornados pela API forem zero. Em caso de falha HTTP (401, 403, 429, 500, indisponibilidade) ou dados ainda não carregados, o Hero DEVE manter o estado de indisponibilidade parcial e oferecer recuperação via retentativa.

### RF-ADM-02 - Analytics do App e Cliques por Ponto
**História:** Como operador do produto, quero saber quais rotas e pontos de apoio foram mais acessados no aplicativo para avaliar a atratividade do conteúdo.

1. O SISTEMA DEVE exibir métricas de sessões, rotas abertas, cliques em contatos/pontos e downloads offline.
2. O SISTEMA DEVE exibir uma lista ranqueada com indicador de barra visual dos pontos de apoio mais clicados na rota selecionada.
3. SE a API não fornecer agregados por ponto O SISTEMA NÃO DEVE apresentar completude cadastral,
   ordem do catálogo ou qualquer outra aproximação como ranking de acesso; a indisponibilidade
   DEVE ser informada explicitamente.
4. QUANDO houver consentimento explícito de analytics O SISTEMA DEVE aceitar exclusivamente os
   eventos `session_opened`, `route_opened`, `contact_opened` e `offline_download_completed`.
5. O SISTEMA DEVE aceitar, por evento, somente as dimensões abaixo: `region_slug` nos quatro
   eventos; `route_slug` em `route_opened`, `contact_opened` e `offline_download_completed`; e
   `support_point_id` técnico, UUID de ator publicado pertencente à rota, somente em
   `contact_opened`. Não DEVE aceitar dimensão, propriedade ou campo adicional.
6. O SISTEMA NÃO DEVE receber, persistir ou expor coordenadas, texto livre, contato do visitante,
   IP, user-agent, identificador de usuário, identificador de sessão, identificador de consentimento
   ou outro identificador pessoal/pseudônimo do visitante. O identificador técnico de ponto não
   identifica visitante e só é usado para a agregação de contatos.
7. QUANDO o consentimento for ausente ou revogado O SISTEMA NÃO DEVE enfileirar, transmitir ou
   contabilizar novos eventos; a revogação DEVE eliminar imediatamente a fila local opcional.
8. O SISTEMA DEVE reter eventos brutos sem identificadores por no máximo 24 horas para depuração
   operacional e expurgá-los automaticamente; agregados diários mínimos podem ser retidos por 13
   meses. A API administrativa DEVE suprimir qualquer métrica, inclusive ranking, com contagem
   inferior a 10 no período consultado.

### RF-ADM-03 - Matriz de Prontidão de Rotas
**História:** Como editor/revisor, quero acompanhar o percentual de prontidão de cada rota antes de publicá-la.

1. O SISTEMA DEVE exibir o estado editorial (`Rascunho`, `Em Revisão`, `Publicado`).
2. O SISTEMA DEVE detalhar as dimensões de prontidão (Conteúdo, GPX, Catálogo, Alertas e Offline).
3. O percentual de prontidão e suas dimensões DEVEM vir de contrato administrativo explícito e
   auditável; campos ausentes na API pública NÃO DEVEM ser convertidos em zero nem usados para
   produzir um score aparente.
4. QUANDO um usuário autorizado consultar a matriz O SISTEMA DEVE retornar, por rota do escopo
   regional, estado editorial, versão publicada, última revisão, contagens de pontos publicados e
   em revisão, contatos públicos verificados, alertas bloqueadores e motivos explícitos.
5. O SISTEMA DEVE calcular prontidão somente quando todas as dimensões aplicáveis forem
   observáveis; caso contrário DEVE retornar `score: null` e o motivo de indisponibilidade.
6. SE houver bloqueador obrigatório — campos públicos obrigatórios, nenhuma etapa, nenhum
   segmento, alerta crítico publicado vigente ou contato público sem verificação — O SISTEMA DEVE
   identificá-lo separadamente e não declarar a rota pronta, independentemente do score.

### RF-ADM-04 - Central de Relatos e Alertas
**História:** Como operador do produto, quero triar avisos enviados por visitantes (trilhas bloqueadas, contatos desatualizados) para manter a plataforma confiável.

1. O SISTEMA DEVE categorizar relatos por urgência (Segurança -> Acesso -> Informação).
2. O SISTEMA DEVE oferecer ações rápidas para resolver ou converter o relato em alteração editorial.

### RF-ADM-05 - Descoberta Externa Isolada
**História:** Como curador, quero usar o Google Places para buscar candidatos sem que essa ferramenta polua o painel principal.

1. A ferramenta de descoberta externa DEVE ficar situada na aba dedicada "Descoberta Externa".
2. Os resultados externos PERMANECEM efêmeros e desvinculados do catálogo publicado até curadoria explícita.

### RF-ADM-06 - Importação CSV por Rota
**História:** Como operador do produto, quero importar planilhas CSV com os pontos de apoio de uma rota específica para agilizar a inclusão em lote.

1. O SISTEMA DEVE permitir o envio de arquivos CSV com a coluna `route_slugs` vinculada à rota alvo.
2. O SISTEMA DEVE apresentar uma prévia de validação indicando linhas válidas, avisos e contatos públicos com proveniência e verificação manual antes de salvar.
3. Os registros importados DEVEM ser salvos exclusivamente como `Rascunho` para revisão humana posterior.

### RF-ADM-07 - Edição Manual Direta e Adição de Pontos
**História:** Como editor, quero editar diretamente no painel qualquer ponto de apoio importado ou adicionar novos pontos manualmente sem precisar de CSV.

1. O SISTEMA DEVE disponibilizar um botão de edição manual (`✏️ Editar`) em cada card de ponto de apoio do catálogo.
2. O SISTEMA DEVE disponibilizar o botão `+ Adicionar Ponto Manual` para cadastrar um novo ponto do zero via formulário modal.
3. A edição manual DEVE atualizar imediatamente a visualização do ponto e seu score de prontidão.
4. A interface SOMENTE DEVE atualizar a visualização depois que a API confirmar a persistência do
   rascunho; falhas HTTP ou de rede não podem ser tratadas como sucesso local.
5. ENQUANTO não existir contrato administrativo para criar ator, localização, contato e vínculo com
   rota em uma única operação segura, o botão de adição manual NÃO DEVE ser apresentado como fluxo
   funcional; novos pontos continuam entrando pelo CSV como rascunhos.

## Requisitos Não Funcionais

### RNF-ADM-01 - Diretrizes TDAH e Acessibilidade
- Informações divididas em blocos visuais claros com bordas delimitadas.
- Cores semânticas acompanhadas de texto explicativo e ícones em todos os estados.
- Suporte total ao tema claro e escuro persistente.
