# Requirements - Painel de acompanhamento do desenvolvimento

> Status: aprovado pelo pedido do responsável de produto em 2026-07-27

## Contexto

O responsável pelo produto precisa acompanhar o desenvolvimento da ECOnexão sem
percorrer manualmente vários arquivos. A apresentação deve reduzir carga cognitiva,
destacar uma ação por vez e tornar bloqueios compreensíveis para uma pessoa com TDAH.

## Escopo

- Aplicação interna em Streamlit, separada da PWA e do painel editorial.
- Leitura automática dos arquivos `.kiro/specs/**/tasks.md`.
- Visão geral, próxima ação recomendada, Kanban e lista de bloqueios.
- Atualização periódica e atualização manual.
- Tema visual alinhado à identidade ECOnexão.

## Histórias e critérios EARS

### RF-DEV-01 - Visão executiva

**História:** Como responsável pelo produto, quero entender o estado do desenvolvimento
em poucos segundos para decidir onde concentrar minha atenção.

1. QUANDO o painel abrir O SISTEMA DEVE mostrar progresso total e contagens de tarefas
   concluídas, em andamento, pendentes e bloqueadas.
2. QUANDO houver trabalho em andamento O SISTEMA DEVE destacá-lo antes do backlog.
3. SE houver bloqueios O SISTEMA DEVE destacá-los sem depender somente de cor.

### RF-DEV-02 - Próxima etapa orientada

**História:** Como responsável pelo produto, quero receber uma recomendação objetiva de
próxima etapa para reduzir a indecisão.

1. QUANDO houver tarefa em andamento O SISTEMA DEVE recomendá-la como foco atual.
2. SE não houver tarefa em andamento O SISTEMA DEVE recomendar a primeira tarefa
   pendente cujas dependências estejam concluídas.
3. SE nenhuma tarefa estiver pronta O SISTEMA DEVE explicar o bloqueio ou a ausência de
   trabalho disponível.
4. A recomendação DEVE informar o motivo e uma ação concreta.

### RF-DEV-03 - Kanban

**História:** Como responsável pelo produto, quero visualizar o fluxo de trabalho em
colunas para reconhecer rapidamente o que mudou.

1. O SISTEMA DEVE organizar tarefas em Pendente, Em desenvolvimento, Bloqueado e Entregue.
2. CADA cartão DEVE mostrar título, spec de origem, requisitos e motivo do bloqueio quando
   disponível.
3. O usuário DEVE poder filtrar por spec, wave/seção e texto.

### RF-DEV-04 - Sincronização automática

**História:** Como responsável pelo produto, quero que o painel acompanhe os artefatos de
execução sem uma segunda fonte manual.

1. QUANDO um `tasks.md` for alterado O SISTEMA DEVE refletir a mudança na atualização
   periódica seguinte.
2. O SISTEMA DEVE oferecer atualização manual imediata.
3. O painel DEVE informar o horário da última leitura e o intervalo ativo.
4. O SISTEMA NÃO DEVE escrever em `tasks.md`.

## Requisitos não funcionais

### RNF-DEV-01 - Acessibilidade e TDAH

- Uma mensagem principal por bloco, títulos objetivos, espaço visual e detalhes sob demanda.
- Estados usam texto, ícone e cor.
- Navegação por teclado, contraste WCAG 2.2 AA e respeito a movimento reduzido.
- O resumo essencial deve permanecer compreensível sem gráficos.

### RNF-DEV-02 - Segurança

- O leitor permanece limitado a `.kiro/specs/**/tasks.md`.
- Nenhum segredo ou arquivo `.env` é lido ou exibido.
- A aplicação é uma ferramenta local e não concede acesso ao painel editorial.

### RNF-DEV-03 - Manutenibilidade

- Parser, priorização e interface devem ter responsabilidades separadas.
- A interpretação dos estados deve seguir as convenções do `AGENTS.md`.
- Regras centrais de parsing e recomendação devem possuir testes automatizados.

