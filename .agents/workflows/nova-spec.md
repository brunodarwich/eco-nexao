---
title: Nova spec
description: Cria uma feature spec no formato requirements, design e tasks.
---

# /nova-spec

1. Leia `@/AGENTS.md`, `@/.kiro/steering/` e `@/spec/README.md`.
2. Converta o pedido em um slug curto e crie `@/.kiro/specs/<slug>/`.
3. Gere `requirements.md` a partir de `@/.kiro/templates/requirements.md`, usando histórias e critérios EARS testáveis.
4. Pare para revisão humana dos requisitos.
5. Após aprovação, gere `design.md` a partir de `@/.kiro/templates/design.md`, cobrindo arquitetura, dados, interfaces, erros, segurança, acessibilidade e testes.
6. Pare para revisão humana do design.
7. Após aprovação, gere `tasks.md` a partir de `@/.kiro/templates/tasks.md`, com dependências e rastreabilidade.
8. Não implemente até a aprovação explícita da lista de tarefas.

