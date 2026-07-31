# Design — documentação e organização do repositório

## Hierarquia de autoridade

1. `.kiro/steering/`: princípios permanentes;
2. `.kiro/specs/`: comportamento e tarefas aprovadas;
3. `spec/`: especificação consolidada de produto e técnica;
4. `docs/`: guias, operação, apresentações e evidências;
5. README de cada componente: instruções locais.

Em conflito, prevalece o item de menor número. Rascunhos e apresentações não são
normativos.

## Taxonomia

```text
docs/
├── README.md                 # catálogo e regras de manutenção
├── architecture/overview.md # mapa do sistema implementado
├── development/setup.md     # instalação, execução e validação
├── operations/pindobal.md   # seed, inventário e descoberta editorial
├── apresentacoes/            # materiais institucionais
├── design-proposals/         # propostas visuais
└── visual-evidence/          # capturas de verificação
```

O README da raiz funciona como landing page, não como manual exaustivo. Dados brutos e
saídas permanecem nos caminhos atuais nesta tarefa porque comandos e registros já os
referenciam; sua função é documentada em vez de realizar uma migração potencialmente
incompatível.

## Segurança e privacidade

- Referenciar somente `.env.example`; nunca inspecionar nem documentar valores de `.env`.
- Credenciais permanecem server-side e sem prefixo `NEXT_PUBLIC_`.
- A documentação do inventário reforça revisão humana e ausência de publicação automática.

## Acessibilidade

Markdown usa títulos hierárquicos, texto de links significativo e tabelas pequenas. Imagens
de evidência são catalogadas por finalidade; seu conteúdo não é requisito para compreender
as instruções operacionais.

## Verificação

- `pnpm exec prettier --check` nos Markdown alterados;
- verificador local de links relativos nos Markdown alterados;
- conferência dos comandos contra `package.json` e `pyproject.toml`;
- `git diff --check`.

## Rastreabilidade

| Requisito | Entrega |
|---|---|
| RF-DOC-01 | `README.md`, `docs/development/setup.md` |
| RF-DOC-02 | `docs/README.md` |
| RF-DOC-03 | `docs/architecture/overview.md`, `docs/operations/pindobal.md` |
| RF-DOC-04 | spec, verificações registradas em `tasks.md` |
