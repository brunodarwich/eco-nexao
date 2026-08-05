# Prompt de continuidade — cadastro manual de ponto de apoio

Trabalhe no repositório ECOnexão seguindo integralmente o `AGENTS.md` e os artefatos em `.kiro/`.

Continue a implementação da spec:

- `.kiro/specs/cadastro-manual-ponto-apoio/requirements.md`
- `.kiro/specs/cadastro-manual-ponto-apoio/design.md`
- `.kiro/specs/cadastro-manual-ponto-apoio/tasks.md`

Leia novamente todos os arquivos de steering e as specs `plataforma-mvp`, `revisao-pos-mvp` e
`painel-operacional` antes de agir. Preserve mudanças preexistentes e não leia nem exponha `.env`,
URLs com credenciais ou outros segredos.

## Estado confirmado em 2026-08-05

- Tasks 1 a 3 da nova spec estão concluídas.
- Task 4 está `[~]`; subtasks 4.1 a 4.4 estão implementadas e verificadas.
- Backend local: 275 testes aprovados e 1 teste concorrente ignorado por exigir PostgreSQL/PostGIS.
- Respostas HTTP reais `201/400/401/403/409/429/500` passaram contra o OpenAPI.
- Ruff, `makemigrations --check --dry-run` e sincronização OpenAPI/TypeScript passaram.
- O Supabase `econexao`, projeto `hjtkcmbfndbgyurfhsuo`, está `ACTIVE_HEALTHY`, em PostgreSQL 17,
  região `sa-east-1`.
- O banco remoto possui até `catalog 0002` e `audit 0003`; ainda faltam:
  - `services/api/modules/catalog/migrations/0003_supportpointidempotencyrecord.py`;
  - `services/api/modules/catalog/migrations/0004_contact_provenance.py`;
  - `services/api/modules/audit/migrations/0004_alter_auditevent_action.py`.

## Autorização humana explícita

O responsável autorizou aplicar essas três migrations no projeto Supabase `econexao` para concluir
a verificação. Essa autorização não permite apagar dados, resetar o banco, expor segredos, aplicar
outras migrations, publicar conteúdo ou alterar outros projetos.

Também está aprovado que:

- somente contatos públicos e verificados são armazenados;
- não se exige autorização do titular;
- a equipe audita várias fontes e consolida os dados em planilha;
- cada contato registra proveniência, data e responsável pela verificação;
- Google pode originar candidatos, mas evidência exclusivamente Google permanece em quarentena
  até conferência humana com fonte independente;
- divergências são resolvidas manualmente;
- toda criação/importação entra como rascunho e somente humanos publicam;
- Santarém é contexto inicial, nunca regra fixa do domínio multirregional.

## Próxima ação obrigatória

1. Verifique que o destino é exatamente `hjtkcmbfndbgyurfhsuo` e que não existe drift remoto.
2. Obtenha a conexão por mecanismo seguro já configurado. Não leia `.env` nem imprima a URL.
3. Revise o SQL das três migrations e a reversibilidade antes de aplicá-las.
4. Aplique somente essas migrations pelo fluxo Django oficial, preservando `django_migrations`.
   Não replique manualmente o SQL pelo MCP e não use reset, `--fake` ou comandos destrutivos.
5. Verifique migrations aplicadas, constraints e RLS. Execute advisors de segurança do Supabase.
6. Execute o teste
   `modules/catalog/test_support_point_validation.py::test_concurrent_keys_serialize_duplicate_check_on_postgresql`
   em ambiente isolado de teste. Não permita que o runner crie, limpe ou altere dados editoriais
   compartilhados. Se não houver isolamento seguro, pare e registre o bloqueio em vez de testar no
   banco compartilhado.
7. Registre evidências em `tasks.md`. Só marque a Task 4 `[x]` se concorrência, rollback e migrations
   estiverem efetivamente verificados.
8. Depois da Task 4 concluída, implemente a Task 5 na ordem definida, com testes frontend e
   acessibilidade. Em seguida execute Task 6/V1–V5 e somente então Task 7.

## Regras de fechamento

- Não marque `revisao-pos-mvp` 9.7 nem `painel-operacional` 8.3 como concluídas antes de V1–V5,
  frontend, E2E, ausência de publicação automática e rastreabilidade estarem comprovados.
- Não transforme a planilha consolidada em substituta silenciosa do cadastro manual: importação em
  lote e cadastro unitário compartilham regras, mas continuam fluxos distintos.
- Não altere decisões de produto silenciosamente. Registre qualquer nova decisão como pendência
  bloqueadora.

Ao final da sessão, apresente:

1. migrations aplicadas e evidências;
2. resultado do teste concorrente;
3. tasks concluídas e ainda abertas;
4. arquivos modificados;
5. riscos ou decisões humanas restantes;
6. próxima task implementável.
