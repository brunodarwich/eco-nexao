# Requirements - Painel Operacional Administrativo (Reflexo do App)

> Status: Proposta criada para aprovação do responsável de produto em 2026-07-31

## Contexto

O painel administrativo (`apps/admin`) exibia como tela principal a ferramenta de consulta de candidatos do Google Places. O responsável pelo produto (com perfil TDAH) precisa de um painel operacional que seja o reflexo real do aplicativo ECOnexão: exibindo engajamento de visitantes, rotas mais acessadas, pontos de apoio mais clicados, estado editorial de publicação e alertas da comunidade, reduzindo sobrecarga cognitiva e orientando a ação prioritária.

## Escopo

- Redesenho completo da tela principal de `apps/admin`.
- Navegação estruturada em 4 abas claras: Métricas do App, Rotas & Prontidão, Central de Relatos & Alertas, e Descoberta Externa (Google Places).
- Hero Card de Foco Recomendado no topo ("Próxima Ação Prioritária").
- Métricas e ranqueamento de engajamento dos pontos/estágios das rotas.
- Acessibilidade WCAG 2.2 AA e perspicuidade visual para TDAH (ícone + texto + cor).

## Histórias e critérios EARS

### RF-ADM-01 - Foco Recomendado (TDAH)
**História:** Como operador do produto, quero ver imediatamente qual a ação prioritária do dia ao abrir o painel para não me sentir sobrecarregado.

1. QUANDO o painel operacional for aberto O SISTEMA DEVE exibir no topo um card de Hero com a ação prioritária recomendada.
2. SE houver alertas de segurança ou rotas pendentes O SISTEMA DEVE destacá-los com atalhos diretos de ação.

### RF-ADM-02 - Analytics do App e Cliques por Ponto
**História:** Como operador do produto, quero saber quais rotas e pontos de apoio foram mais acessados no aplicativo para avaliar a atratividade do conteúdo.

1. O SISTEMA DEVE exibir métricas de sessões, rotas abertas, cliques em contatos/pontos e downloads offline.
2. O SISTEMA DEVE exibir uma lista ranqueada com indicador de barra visual dos pontos de apoio mais clicados na rota selecionada.

### RF-ADM-03 - Matriz de Prontidão de Rotas
**História:** Como editor/revisor, quero acompanhar o percentual de prontidão de cada rota antes de publicá-la.

1. O SISTEMA DEVE exibir o estado editorial (`Rascunho`, `Em Revisão`, `Publicado`).
2. O SISTEMA DEVE detalhar as dimensões de prontidão (Conteúdo, GPX, Catálogo, Alertas e Offline).

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
2. O SISTEMA DEVE apresentar uma prévia de validação indicando linhas válidas, avisos e contatos autorizados antes de salvar.
3. Os registros importados DEVEM ser salvos exclusivamente como `Rascunho` para revisão humana posterior.

### RF-ADM-07 - Edição Manual Direta e Adição de Pontos
**História:** Como editor, quero editar diretamente no painel qualquer ponto de apoio importado ou adicionar novos pontos manualmente sem precisar de CSV.

1. O SISTEMA DEVE disponibilizar um botão de edição manual (`✏️ Editar`) em cada card de ponto de apoio do catálogo.
2. O SISTEMA DEVE disponibilizar o botão `+ Adicionar Ponto Manual` para cadastrar um novo ponto do zero via formulário modal.
3. A edição manual DEVE atualizar imediatamente a visualização do ponto e seu score de prontidão.

## Requisitos Não Funcionais

### RNF-ADM-01 - Diretrizes TDAH e Acessibilidade
- Informações divididas em blocos visuais claros com bordas delimitadas.
- Cores semânticas acompanhadas de texto explicativo e ícones em todos os estados.
- Suporte total ao tema claro e escuro persistente.
