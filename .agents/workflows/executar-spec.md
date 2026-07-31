---
title: Executar spec
description: Executa tarefas aprovadas de uma spec com verificação entre etapas.
---

# /executar-spec

1. Solicite ou identifique o slug da spec.
2. Leia os três artefatos da spec e confira se não há lacunas ou contradições.
3. Selecione a primeira tarefa `[ ]` cujas dependências estejam concluídas.
4. Marque-a `[~]`, implemente apenas seu escopo e execute as verificações previstas.
5. Se as verificações passarem, marque `[x]` e registre evidências; se falharem, mantenha `[~]`; se depender de decisão externa, marque `[!]`.
6. Repita enquanto houver tarefas executáveis.
7. Ao final, faça uma verificação integrada contra todos os critérios de aceite e produza um resumo de entrega.

