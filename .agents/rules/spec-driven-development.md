---
trigger: always_on
description: Aplicar sempre o fluxo ECOnexão de requirements, design e tasks antes de implementar.
---

# Desenvolvimento orientado por especificação

Este workspace usa um fluxo compatível com Kiro. A fonte de verdade está em `@/.kiro/`.

Antes de propor ou alterar código:

1. Leia `@/AGENTS.md`.
2. Leia os arquivos aplicáveis em `@/.kiro/steering/`.
3. Localize a spec ativa em `@/.kiro/specs/`.
4. Valide a cadeia `requirements.md` -> `design.md` -> `tasks.md`.

Não implemente comportamento ausente dos requisitos. Não introduza decisão arquitetural ausente do design. Trabalhe somente em tarefa aberta e respeite dependências.

Ao iniciar uma tarefa, troque `[ ]` por `[~]`. Ao terminar, rode as verificações descritas e só então troque por `[x]`, acrescentando evidências concisas. Se houver bloqueio, use `[!]` e registre o motivo.

Quando o pedido alterar o escopo:

1. atualize requisitos e critérios de aceite;
2. ajuste o design e a rastreabilidade;
3. regenere as tarefas afetadas;
4. peça revisão humana antes da implementação se houver mudança material de produto, segurança, privacidade, custo ou arquitetura.

Use os workflows `/nova-spec`, `/executar-spec` e `/sincronizar-spec` para operações recorrentes.
